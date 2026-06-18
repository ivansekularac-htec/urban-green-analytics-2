"""
superuser_service.py
Startup service for ensuring initial superuser exists.
"""

import logging
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models.users.role import Role
from app.models.users.user import User
from app.models.users.user_roles import UserRole
from app.security.password import hash_password

logger = logging.getLogger(__name__)

ADMIN_ROLE_NAME = "Admin"


def ensure_superuser(
    session_factory: Callable[[], Session] = SessionLocal,
) -> None:
    """Create the admin user and assign the Admin role if it doesn't exist."""
    settings = get_settings()

    with session_factory() as db:
        admin_role = db.scalar(
            select(Role).where(Role.name == ADMIN_ROLE_NAME),
        )

        if admin_role is None:
            logger.warning(
                "Admin role not found in DB; skipping superuser seed.",
            )
            return

        existing_user = db.scalar(
            select(User).where(User.email == settings.superuser_email),
        )

        if existing_user is not None:
            logger.info(
                "Superuser %s already present; skipping.",
                settings.superuser_email,
            )
            return

        user = User(
            email=settings.superuser_email,
            full_name=settings.superuser_full_name,
            password_hash=hash_password(settings.superuser_password),
            is_active=True,
        )

        db.add(user)
        db.flush()

        db.add(
            UserRole(
                user_id=user.id,
                role_id=admin_role.id,
                farm_id=None,
            ),
        )

        db.commit()

        logger.info(
            "Seeded superuser %s with Admin role.",
            settings.superuser_email,
        )
