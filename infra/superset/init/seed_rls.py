"""Seed email-based farm row-level security for all dashboard datasets."""

from __future__ import annotations

from superset.app import create_app

RLS_NAME = "Farm access by Superset email"

RLS_CLAUSE = """
    farm_id IN
        (
            SELECT access.farm_id
            FROM
            (
                SELECT
                    user_id,
                    farm_id
                FROM urbangreen_dw.dim_user_farm_role FINAL
                WHERE is_current = 1
                AND farm_id != 0
            ) AS access
            INNER JOIN
            (
                SELECT
                    user_id,
                    email
                FROM urbangreen_dw.dim_user FINAL
                WHERE is_active = 1
            ) AS users
                ON access.user_id = users.user_id
            WHERE lowerUTF8(users.email) = lowerUTF8('{{ current_user_email() }}')
        )
    """.strip()


def seed_farm_rls() -> None:
    """Create or update farm RLS for all dashboard datasets."""

    app = create_app()

    with app.app_context():
        from superset import db
        from superset.connectors.sqla.models import (
            RowLevelSecurityFilter,
        )
        from superset.models.dashboard import Dashboard
        from superset.utils.core import RowLevelSecurityFilterType

        dashboards = db.session.query(Dashboard).all()

        if not dashboards:
            raise RuntimeError("No Superset dashboards were found.")

        datasets_by_id = {}

        for dashboard in dashboards:
            for dataset in dashboard.datasources:
                datasets_by_id[dataset.id] = dataset

        datasets = list(datasets_by_id.values())

        if not datasets:
            raise RuntimeError("Imported dashboards do not use any datasets.")

        missing_farm_id = sorted(
            dataset.table_name
            for dataset in datasets
            if "farm_id" not in dataset.column_names
        )

        if missing_farm_id:
            raise RuntimeError(
                "Datasets without farm_id: " + ", ".join(missing_farm_id)
            )

        security_manager = app.appbuilder.sm

        roles = [
            security_manager.find_role("Manager"),
            security_manager.find_role("Operations Team"),
        ]

        if any(role is None for role in roles):
            raise RuntimeError("Manager and Operations Team roles must exist.")

        rls_filter = (
            db.session.query(RowLevelSecurityFilter)
            .filter_by(name=RLS_NAME)
            .one_or_none()
        )

        if rls_filter is None:
            rls_filter = RowLevelSecurityFilter(name=RLS_NAME)
            db.session.add(rls_filter)

        rls_filter.description = (
            "Restricts dashboard data to farms assigned to the logged-in Superset user."
        )
        rls_filter.filter_type = RowLevelSecurityFilterType.REGULAR.value
        rls_filter.clause = RLS_CLAUSE
        rls_filter.group_key = "farm_access"
        rls_filter.roles = roles
        rls_filter.tables = datasets

        db.session.commit()

        dashboard_names = ", ".join(
            sorted(dashboard.dashboard_title for dashboard in dashboards)
        )

        dataset_names = ", ".join(sorted(dataset.table_name for dataset in datasets))

        print("Farm-level Superset RLS seeded successfully.")
        print(f"Dashboards: {dashboard_names}")
        print(f"Protected datasets: {dataset_names}")


if __name__ == "__main__":
    seed_farm_rls()
