"""
Superuser seeding.

Creates the configured admin user (and assigns the Admin role) on application
startup. Idempotent: a no-op if the user already exists, and a logged warning
(not an error) if the Admin role has not been seeded yet -- which happens on a
fresh database that has not run the Postgres init scripts.
"""

import logging

from sqlalchemy import select

from app.config import Settings, get_settings
from app.database import SessionLocal
from app.models.users.role import Role
from app.models.users.user import User
from app.models.users.user_roles import UserRole
from app.security.password import hash_password

logger = logging.getLogger(__name__)

ADMIN_ROLE_NAME = "Admin"


def _superuser_attributes(settings: Settings) -> dict:
    """Build the User column values for the configured superuser."""
    return {
        "email": settings.superuser_email,
        "full_name": settings.superuser_full_name,
        "password_hash": hash_password(settings.superuser_password),
        "is_active": True,
    }


def ensure_superuser(session_factory=SessionLocal) -> None:
    """
    Create the configured superuser with the Admin role if it does not exist.

    Args:
        session_factory: Callable returning a SQLAlchemy ``Session``. Injected
            so tests can pass a mock factory; defaults to ``SessionLocal``.
    """
    settings = get_settings()

    with session_factory() as db:
        admin_role = db.scalar(select(Role).where(Role.name == ADMIN_ROLE_NAME))

        if admin_role is None:
            logger.warning(
                "Admin role not found in DB; skipping superuser seed. "
                "Did the Postgres init scripts run?"
            )
            return

        existing = db.scalar(select(User).where(User.email == settings.superuser_email))

        if existing is not None:
            logger.info("Superuser %s already present; skipping.", settings.superuser_email)
            return

        user = User(**_superuser_attributes(settings))
        db.add(user)
        db.flush()

        # farm_id left NULL -> global Admin, not scoped to a single farm.
        db.add(UserRole(user_id=user.id, role_id=admin_role.id))
        db.commit()

        logger.info("Seeded superuser %s with Admin role.", settings.superuser_email)
