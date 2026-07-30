"""
Demo user bootstrap.

Ensures Farm Manager and Operations Team demo accounts exist on every
startup so local/dev environments share the same personas. Idempotent:
re-running with the same email does nothing.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.farms.farm import Farm
from app.models.users.role import Role
from app.models.users.user import User
from app.models.users.user_roles import UserRole
from app.security.password import hash_password
from app.security.roles import RoleName

logger = logging.getLogger(__name__)


def _parse_farm_ids(raw: str) -> list[int]:
    return [int(part.strip()) for part in raw.split(",") if part.strip()]


def _require_role(db: Session, role_name: RoleName) -> Role:
    role = db.scalars(select(Role).where(Role.name == role_name.value)).one_or_none()
    if role is None:
        raise RuntimeError(
            f"Cannot create demo user: role '{role_name.value}' is missing. "
            "Run the seed migration first."
        )
    return role


def _require_farm(db: Session, farm_id: int) -> None:
    farm = db.scalars(select(Farm).where(Farm.id == farm_id)).one_or_none()
    if farm is None:
        raise RuntimeError(
            f"Cannot assign demo user to farm_id={farm_id}: farm is missing. "
            "Run the seed migration first."
        )


def _ensure_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    role: Role,
    farm_ids: list[int],
) -> User:
    user = db.scalars(select(User).where(User.email == email)).one_or_none()
    if user is not None:
        logger.info("Demo user %s already exists.", email)
        return user

    for farm_id in farm_ids:
        _require_farm(db, farm_id)

    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        is_active=True,
    )
    db.add(user)
    db.flush()

    for farm_id in farm_ids:
        db.add(UserRole(user_id=user.id, role_id=role.id, farm_id=farm_id))

    db.commit()
    logger.info("Demo user %s created with farms %s.", email, farm_ids)
    return user


def ensure_demo_users(db: Session, settings: Settings) -> tuple[User, User]:
    """Create the configured demo Farm Manager and Operations users if missing."""
    farm_manager_role = _require_role(db, RoleName.FARM_MANAGER)
    ops_role = _require_role(db, RoleName.OPERATIONS_TEAM)

    manager = _ensure_user(
        db,
        email=settings.demo_farm_manager_email,
        password=settings.demo_farm_manager_password,
        full_name=settings.demo_farm_manager_full_name,
        role=farm_manager_role,
        farm_ids=[settings.demo_farm_manager_farm_id],
    )
    ops = _ensure_user(
        db,
        email=settings.demo_ops_email,
        password=settings.demo_ops_password,
        full_name=settings.demo_ops_full_name,
        role=ops_role,
        farm_ids=_parse_farm_ids(settings.demo_ops_farm_ids),
    )
    return manager, ops
