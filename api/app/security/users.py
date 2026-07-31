"""
Dashboard user bootstrap.

Ensures one Farm Manager account and one Operations Team account exist on
every startup. Farm assignments are selected randomly when each user is
created for the first time.

Idempotent: re-running with the same email does nothing.
"""

import logging

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.users.role import Role
from app.models.users.user import User
from app.models.users.user_roles import UserRole
from app.security.password import hash_password
from app.security.roles import RoleName

logger = logging.getLogger(__name__)

FARM_MANAGER_FARM_COUNT = 1
OPERATIONS_TEAM_FARM_COUNT = 15


def _get_random_farm_ids(
    db: Session,
    farm_count: int,
) -> list[int]:
    """Return random IDs of existing farms."""

    farm_ids = list(
        db.scalars(
            text(
                """
                SELECT id
                FROM app.farms
                ORDER BY random()
                LIMIT :farm_count
                """
            ),
            {"farm_count": farm_count},
        ).all()
    )

    if len(farm_ids) < farm_count:
        raise RuntimeError(
            f"Cannot assign {farm_count} farms because only {len(farm_ids)} farms exist."
        )

    return farm_ids


def _ensure_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    role_name: RoleName,
    farm_count: int,
) -> User | None:
    """Create one configured user if it does not already exist."""

    user = db.scalars(select(User).where(User.email == email)).one_or_none()

    if user is not None:
        logger.info(f"User {email} already exists.")
        return user

    role = db.scalars(select(Role).where(Role.name == role_name.value)).one_or_none()

    if role is None:
        logger.warning(f"Skipping demo user {email} because role {role_name.value} is missing.")
        return None

    farm_ids = _get_random_farm_ids(db=db, farm_count=farm_count)

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

    logger.info(
        f"User {email} created with role {role_name.value} for farms: {', '.join(str(farm_id) for farm_id in farm_ids)}."
    )

    return user


def ensure_users(
    db: Session,
    settings: Settings,
) -> tuple[User | None, User | None]:
    """Create the configured Farm Manager and Operations Team users."""

    farm_manager = _ensure_user(
        db,
        email=settings.farm_manager_email,
        password=settings.farm_manager_password,
        full_name=settings.farm_manager_full_name,
        role_name=RoleName.FARM_MANAGER,
        farm_count=FARM_MANAGER_FARM_COUNT,
    )

    operations_user = _ensure_user(
        db,
        email=settings.operations_team_email,
        password=settings.operations_team_password,
        full_name=settings.operations_team_full_name,
        role_name=RoleName.OPERATIONS_TEAM,
        farm_count=OPERATIONS_TEAM_FARM_COUNT,
    )

    return farm_manager, operations_user
