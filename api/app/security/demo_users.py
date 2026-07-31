"""
Demo user bootstrap.

Ensures Farm Manager and Operations Team demo accounts exist on every
startup so local/dev environments share the same personas. Idempotent:
creates missing users and reconciles farm grants when they drift.
Missing roles or farms are logged and skipped — never blocks API startup.
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


def _get_role(db: Session, role_name: RoleName) -> Role | None:
    role = db.scalars(select(Role).where(Role.name == role_name.value)).one_or_none()
    if role is None:
        logger.warning(
            "Demo seeding skipped: role %r is missing.",
            role_name.value,
        )
    return role


def _known_farm_ids(db: Session, farm_ids: list[int]) -> list[int]:
    """Keep only farms that exist; log the rest."""
    if not farm_ids:
        return []
    found = set(db.scalars(select(Farm.id).where(Farm.id.in_(farm_ids))).all())
    kept = []
    for farm_id in farm_ids:
        if farm_id in found:
            kept.append(farm_id)
        else:
            logger.warning("Demo farm_id=%s missing; skipping.", farm_id)
    return kept


def _ensure_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    role: Role,
    farm_ids: list[int],
) -> None:
    farm_ids = _known_farm_ids(db, farm_ids)

    user = db.scalars(select(User).where(User.email == email)).one_or_none()

    if user is None:
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
        return

    # Existing user: reconcile grants (same idea as Superset role drift fix).
    current = list(
        db.scalars(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == role.id,
            )
        ).all()
    )
    current_ids = {row.farm_id for row in current}
    desired_ids = set(farm_ids)

    if current_ids == desired_ids:
        logger.info("Demo user %s skipped.", email)
        return

    for row in current:
        if row.farm_id not in desired_ids:
            db.delete(row)
    for farm_id in desired_ids - current_ids:
        db.add(UserRole(user_id=user.id, role_id=role.id, farm_id=farm_id))

    db.commit()
    logger.info("Demo user %s grants updated to %s.", email, sorted(desired_ids))


def ensure_demo_users(db: Session, settings: Settings) -> None:
    """Create/reconcile the configured demo Farm Manager and Operations users."""
    fm_role = _get_role(db, RoleName.FARM_MANAGER)
    if fm_role is not None:
        _ensure_user(
            db,
            email=settings.demo_farm_manager_email,
            password=settings.demo_farm_manager_password,
            full_name=settings.demo_farm_manager_full_name,
            role=fm_role,
            farm_ids=[settings.demo_farm_manager_farm_id],
        )

    ops_role = _get_role(db, RoleName.OPERATIONS_TEAM)
    if ops_role is not None:
        _ensure_user(
            db,
            email=settings.demo_ops_email,
            password=settings.demo_ops_password,
            full_name=settings.demo_ops_full_name,
            role=ops_role,
            farm_ids=_parse_farm_ids(settings.demo_ops_farm_ids),
        )
