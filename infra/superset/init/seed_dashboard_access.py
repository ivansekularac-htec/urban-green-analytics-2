"""Seed dashboard access by Superset role."""

from __future__ import annotations

from superset.app import create_app

DASHBOARD_ACCESS = {
    "Executive Overview": ("Manager",),
}


def seed_dashboard_access() -> None:
    """Assign roles to dashboards and publish them."""

    app = create_app()

    with app.app_context():
        from superset import db
        from superset.models.dashboard import Dashboard

        security_manager = app.appbuilder.sm

        for dashboard_title, role_names in DASHBOARD_ACCESS.items():
            dashboard = (
                db.session.query(Dashboard)
                .filter_by(dashboard_title=dashboard_title)
                .one_or_none()
            )

            if dashboard is None:
                raise RuntimeError(f"Dashboard not found: {dashboard_title}")

            roles = []

            for role_name in role_names:
                role = security_manager.find_role(role_name)

                if role is None:
                    raise RuntimeError(f"Superset role not found: {role_name}")

                roles.append(role)

            dashboard.roles = roles
            dashboard.published = True

        db.session.commit()

        print("Dashboard access seeded successfully.")

        for dashboard_title, role_names in DASHBOARD_ACCESS.items():
            print(f"{dashboard_title}: {', '.join(role_names)}")


if __name__ == "__main__":
    seed_dashboard_access()
