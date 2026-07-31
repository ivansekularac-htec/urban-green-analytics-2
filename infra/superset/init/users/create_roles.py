"""
Creates custom Superset roles for the Urban Green BI platform.

This module provisions the application-specific roles required for role-based
access control (RBAC). Business roles inherit the permissions of the built-in
Gamma role, while dedicated RLS roles are created for each active user.
The built-in Admin role is created during the initial Superset bootstrap.
"""

import logging

from users.database import SUPERSET_DATABASE_NAME, get_clickhouse_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BUSINESS_ROLES = [
    "FarmManager",
    "Operations",
]


def load_user_ids():
    """Load active user IDs from ClickHouse."""

    client = get_clickhouse_client()

    result = client.query(
        """
        SELECT
            user_id
        FROM dim_user
        WHERE is_active = 1
        """
    )

    return [row["user_id"] for row in result.named_results()]


def get_rls_role_name(user_id):
    """Return datasets protected by farm-level Row-Level Security."""

    return f"RLS_USER_{user_id}"


def create_roles(app):
    """Create business roles and user-specific RLS roles."""
    sm = app.appbuilder.sm
    from superset.connectors.sqla.models import SqlaTable
    from superset.extensions import db
    from superset.models.core import Database

    gamma = sm.find_role("Gamma")

    if gamma is None:
        raise RuntimeError("Gamma role not found. Run 'superset init' first.")

    database = (
        db.session.query(Database)
        .filter_by(database_name=SUPERSET_DATABASE_NAME)
        .one_or_none()
    )

    database_permission = None

    if database is not None:
        database_permission = sm.find_permission_view_menu(
            "database_access",
            database.perm,
        )

    # Business roles
    for role_name in BUSINESS_ROLES:
        role = sm.find_role(role_name)

        if role is None:
            role = sm.add_role(role_name)
            logger.info(f"Created role {role_name}.")

        existing_permissions = {
            (permission.permission.name, permission.view_menu.name)
            for permission in role.permissions
        }

        # Copy Gamma permissions
        for permission in gamma.permissions:
            key = (
                permission.permission.name,
                permission.view_menu.name,
            )

            if key not in existing_permissions:
                sm.add_permission_role(role, permission)

        if database_permission is not None:
            sm.add_permission_role(role, database_permission)

        for dataset in db.session.query(SqlaTable).all():
            datasource_permission = sm.find_permission_view_menu(
                "datasource_access",
                dataset.perm,
            )

            if datasource_permission is not None:
                sm.add_permission_role(role, datasource_permission)

        logger.info(f"Assigned permissions to role {role_name}.")

    # RLS roles
    for user_id in load_user_ids():
        role_name = get_rls_role_name(user_id)

        if sm.find_role(role_name):
            continue

        sm.add_role(role_name)

        logger.info(f"Created RLS role {role_name}.")
