"""
Seed demo application users used for local development and demos.

These accounts must mirror the demo users created in Superset
(same email addresses, roles, and farm access) so authentication
and Row-Level Security behave consistently across both systems.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.users.role import Role
from app.models.users.user import User
from app.models.users.user_roles import UserRole
from app.security.password import hash_password
from app.security.roles import RoleName

logger = logging.getLogger(__name__)


def ensure_demo_users(db: Session, settings: Settings) -> None:
    users = [
        (
            settings.demo_farm_manager_email,
            settings.demo_farm_manager_password,
            f"{settings.demo_farm_manager_firstname} {settings.demo_farm_manager_lastname}",
            RoleName.FARM_MANAGER,
            [1],  # farms 1
        ),
        (
            settings.demo_operations_email,
            settings.demo_operations_password,
            f"{settings.demo_operations_firstname} {settings.demo_operations_lastname}",
            RoleName.OPERATIONS_TEAM,
            list(range(1, 16)),  # farms 1-15
        ),
    ]

    for email, password, full_name, role_name, farm_ids in users:
        user = db.scalars(select(User).where(User.email == email)).one_or_none()
        if user is not None:
            logger.info(f"Demo user {email} already exists.")
            continue

        role = db.scalars(select(Role).where(Role.name == role_name.value)).one_or_none()
        if role is None:
            logger.warning(
                "Skipping demo user %s: role '%s' does not exist.",
                email,
                role_name.value,
            )
            continue

        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            is_active=True,
        )
        db.add(user)
        db.flush()

        for farm_id in farm_ids:
            db.add(
                UserRole(
                    user_id=user.id,
                    role_id=role.id,
                    farm_id=farm_id,
                )
            )

        db.commit()

        logger.info("Demo user %s created.", email)
