"""
Creates and synchronizes Row-Level Security (RLS) policies for the Urban Green
BI platform.

This module loads farm assignments from the Urban Green data warehouse and
creates or updates Superset Row-Level Security filters. Each user-specific RLS
role is assigned a filter restricting visibility to the farms managed by that
user.
"""

import logging

from users.common import execute_query, get_rls_filter_name, get_rls_role_name

logger = logging.getLogger(__name__)


def load_user_farms():
    """Load active farm assignments grouped by user."""

    result = execute_query(
        """
        SELECT
            u.user_id,
            u.email,
            ufr.farm_id
        FROM dim_user u
        JOIN dim_user_farm_role ufr
            ON u.user_id = ufr.user_id
        WHERE
            u.is_active = 1
            AND ufr.is_current = 1
            AND ufr.farm_id != 0
        """
    )

    users = {}

    for row in result:
        if row["user_id"] not in users:
            users[row["user_id"]] = {
                "email": row["email"],
                "farm_ids": [],
            }

        users[row["user_id"]]["farm_ids"].append(row["farm_id"])

    return users


def get_rls_datasets():
    """Return datasets containing the farm_id column."""
    from superset.connectors.sqla.models import SqlaTable
    from superset.extensions import db

    datasets = db.session.query(SqlaTable).all()

    return [
        dataset
        for dataset in datasets
        if any(column.column_name == "farm_id" for column in dataset.columns)
    ]


def build_clause(farm_ids):
    """Build an SQL RLS clause from a list of farm IDs."""

    farm_ids = sorted(set(farm_ids))

    values = ",".join(map(str, farm_ids))

    return f"farm_id IN ({values})"


def create_or_update_rls(app):
    """Create or update user-specific Row-Level Security filters."""
    from superset.connectors.sqla.models import (
        RowLevelSecurityFilter,
    )
    from superset.extensions import db

    users = load_user_farms()

    sm = app.appbuilder.sm

    datasets = get_rls_datasets()

    for user_id, user in users.items():
        role_name = get_rls_role_name(user_id)
        filter_name = get_rls_filter_name(user_id)

        role = sm.find_role(role_name)

        if role is None:
            raise RuntimeError(f"RLS role '{role_name}' not found.")

        clause = build_clause(user["farm_ids"])

        rls = (
            db.session.query(RowLevelSecurityFilter)
            .filter_by(name=filter_name)
            .one_or_none()
        )

        if rls is None:
            rls = RowLevelSecurityFilter(
                # name=get_rls_filter_name(user_id),
                name=filter_name,
                description=f"Farm access for {user['email']}",
                filter_type="Regular",
                # group_key=get_rls_role_name(user_id),
                group_key=role_name,
                clause=clause,
            )

            db.session.add(rls)

            logger.info(f"Created RLS filter for {user['email']}.")

        else:
            rls.clause = clause

            logger.info(f"Updated RLS filter for {user['email']}.")

        rls.roles = [role]
        rls.tables = datasets

    db.session.commit()

    logger.info("Row-Level Security synchronization completed.")
