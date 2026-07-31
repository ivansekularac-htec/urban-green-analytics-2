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


def ensure_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    role_name: RoleName,
    farm_ids: list[int] | None = None,
) -> User:
    """Create a bootstrap user if it does not already exist."""

    user = db.scalars(select(User).where(User.email == email)).one_or_none()
    if user is not None:
        logger.info("Bootstrap user %s already exists.", email)
        return user

    role = db.scalars(select(Role).where(Role.name == role_name.value)).one_or_none()
    if role is None:
        raise RuntimeError(f"Role '{role_name.value}' not found.")

    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        is_active=True,
    )
    db.add(user)
    db.flush()

    if farm_ids:
        for farm_id in farm_ids:
            db.add(
                UserRole(
                    user_id=user.id,
                    role_id=role.id,
                    farm_id=farm_id,
                )
            )
    else:
        db.add(
            UserRole(
                user_id=user.id,
                role_id=role.id,
                farm_id=None,
            )
        )

    db.commit()

    logger.info("Bootstrap user %s created.", email)
    return user


def ensure_superuser(db: Session, settings: Settings) -> User:
    return ensure_user(
        db,
        email=settings.superuser_email,
        password=settings.superuser_password,
        full_name=settings.superuser_full_name,
        role_name=RoleName.ADMIN,
    )


def ensure_operations_user(db: Session, settings: Settings) -> User:
    return ensure_user(
        db,
        email=settings.operations_email,
        password=settings.operations_password,
        full_name=settings.operations_full_name,
        role_name=RoleName.OPERATIONS_TEAM,
        farm_ids=settings.operations_farm_ids,
    )


def ensure_farm_manager(db: Session, settings: Settings) -> User:
    return ensure_user(
        db,
        email=settings.farm_manager_email,
        password=settings.farm_manager_password,
        full_name=settings.farm_manager_full_name,
        role_name=RoleName.FARM_MANAGER,
        farm_ids=settings.farm_manager_farm_ids,
    )
