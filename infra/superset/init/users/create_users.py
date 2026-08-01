"""
Creates and synchronizes Superset users for the Urban Green BI platform.

This module loads active users and their current business roles from the
Urban Green data warehouse and provisions the corresponding users in
Superset.

Only missing users are created, making the synchronization idempotent.
Each user is assigned:
    - one business role (Admin, FarmManager or Operations)
    - one dedicated RLS role (RLS_USER_<user_id>)
"""

import logging
import os

from users.common import ROLE_MAPPING, execute_query, get_rls_role_name

logger = logging.getLogger(__name__)

ADMIN_EMAIL = os.getenv("SUPERSET_ADMIN_EMAIL", "admin@example.com")
DEFAULT_PASSWORD = os.environ["SUPERSET_DEFAULT_USER_PASSWORD"]


def load_users():
    """Load active users and their current roles from ClickHouse."""

    return execute_query(
        """
        SELECT
            u.user_id,
            u.email,
            u.full_name,
            ufr.role_name
        FROM dim_user u
        JOIN dim_user_farm_role ufr
            ON u.user_id = ufr.user_id
        WHERE
            u.is_active = 1
            AND ufr.is_current = 1
        """
    )


def create_users(app):
    """Create missing Superset users."""
    sm = app.appbuilder.sm

    users = load_users()

    for user in users:
        if user["email"] == ADMIN_EMAIL:
            continue

        superset_user = sm.find_user(username=user["email"])

        parts = user["full_name"].split(maxsplit=1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

        role_name = ROLE_MAPPING.get(user["role_name"])
        if role_name is None:
            raise RuntimeError(f"Unknown role '{user['role_name']}'.")

        business_role = sm.find_role(role_name)
        if business_role is None:
            raise RuntimeError(f"Business role '{role_name}' not found.")

        rls_role_name = get_rls_role_name(user["user_id"])
        rls_role = sm.find_role(rls_role_name)
        if rls_role is None:
            raise RuntimeError(f"RLS role '{rls_role_name}' not found.")

        roles = [
            business_role,
            rls_role,
        ]

        if superset_user is None:
            sm.add_user(
                username=user["email"],
                first_name=first_name,
                last_name=last_name,
                email=user["email"],
                role=roles,
                password=DEFAULT_PASSWORD,
            )

            logger.info(f"Created user {user['email']}.")

        else:
            superset_user.first_name = first_name
            superset_user.last_name = last_name
            superset_user.email = user["email"]
            superset_user.roles = roles

            logger.info(f"Updated user {user['email']}.")

    sm.get_session.commit()
