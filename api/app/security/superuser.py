"""
Superuser bootstrap.

Ensures a system administrator account exists on every startup so the
application is usable from a fresh database. Idempotent: re-running with
the same email does nothing.
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


def ensure_superuser(db: Session, settings: Settings) -> User:
    """Create the configured superuser if it doesn't already exist.

    Returns the user (created or existing) for tests and logging.
    """
    user = db.scalars(select(User).where(User.email == settings.superuser_email)).one_or_none()
    if user is not None:
        logger.info("Superuser %s already exists.", settings.superuser_email)
        return user

    admin_role = db.scalars(select(Role).where(Role.name == RoleName.ADMIN.value)).one_or_none()
    if admin_role is None:
        raise RuntimeError(
            f"Cannot create superuser: role '{RoleName.ADMIN.value}' is missing. "
            "Run the seed migration first."
        )

    user = User(
        email=settings.superuser_email,
        password_hash=hash_password(settings.superuser_password),
        full_name=settings.superuser_full_name,
        is_active=True,
    )
    db.add(user)
    db.flush()

    db.add(UserRole(user_id=user.id, role_id=admin_role.id, farm_id=None))
    db.commit()

    logger.info("Superuser %s created.", settings.superuser_email)
    return user
