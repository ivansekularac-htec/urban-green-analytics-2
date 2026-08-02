"""
Creates custom Superset roles for the Urban Green BI platform.

This module provisions the application-specific roles required for role-based
access control (RBAC). Business roles inherit the permissions of the built-in
Gamma role, while dedicated RLS roles are created for each active user.
The built-in Admin role is created during the initial Superset bootstrap.
"""

import logging

from users.common import (
    BUSINESS_ROLES,
    DATASET_ROLE_MAPPING,
    SUPERSET_DATABASE_NAME,
    execute_query,
    get_rls_role_name,
)

logger = logging.getLogger(__name__)


def load_user_ids():
    """Load active user IDs from ClickHouse."""

    return [
        row["user_id"]
        for row in execute_query(
            """
            SELECT user_id
            FROM dim_user
            WHERE is_active = 1
            """
        )
    ]


def create_roles(app):
    """Create business roles and user-specific RLS roles."""

    from superset.connectors.sqla.models import SqlaTable
    from superset.extensions import db
    from superset.models.core import Database

    sm = app.appbuilder.sm

    gamma = sm.find_role("Gamma")
    if gamma is None:
        raise RuntimeError("Gamma role not found. Run 'superset init' first.")

    database = (
        db.session.query(Database)
        .filter_by(database_name=SUPERSET_DATABASE_NAME)
        .one_or_none()
    )

    database_permission = (
        sm.find_permission_view_menu("database_access", database.perm)
        if database
        else None
    )

    datasets = db.session.query(SqlaTable).all()

    for role_name in BUSINESS_ROLES:
        role = sm.find_role(role_name)

        if role is None:
            role = sm.add_role(role_name)
            logger.info("Created role %s.", role_name)

        existing_permissions = {
            (
                permission.permission.name,
                permission.view_menu.name,
            )
            for permission in role.permissions
        }

        # Inherit all Gamma permissions
        for permission in gamma.permissions:
            key = (
                permission.permission.name,
                permission.view_menu.name,
            )
            if key not in existing_permissions:
                sm.add_permission_role(role, permission)
                existing_permissions.add(key)

        # Grant database access
        if database_permission:
            key = (
                database_permission.permission.name,
                database_permission.view_menu.name,
            )

            if key not in existing_permissions:
                sm.add_permission_role(role, database_permission)
                existing_permissions.add(key)

        # Grant datasource access only to mapped datasets
        for dataset in datasets:
            allowed_roles = DATASET_ROLE_MAPPING.get(dataset.table_name, [])
            if role_name not in allowed_roles:
                continue

            datasource_permission = sm.find_permission_view_menu(
                "datasource_access", dataset.perm
            )
            if datasource_permission is None:
                logger.warning(
                    "Datasource permission not found for %s.",
                    dataset.table_name,
                )
                continue

            key = (
                datasource_permission.permission.name,
                datasource_permission.view_menu.name,
            )
            if key not in existing_permissions:
                sm.add_permission_role(role, datasource_permission)
                existing_permissions.add(key)

        logger.info("Assigned permissions to role %s.", role_name)

    for user_id in load_user_ids():
        role_name = get_rls_role_name(user_id)

        if sm.find_role(role_name) is None:
            sm.add_role(role_name)
            logger.info("Created RLS role %s.", role_name)
