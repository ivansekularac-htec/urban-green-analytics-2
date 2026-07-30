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
            logger.info("Demo user %s already exists.", email)
            continue

        role = db.scalars(select(Role).where(Role.name == role_name.value)).one_or_none()
        if role is None:
            raise RuntimeError(f"Cannot create demo user: role '{role_name.value}' is missing.")

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
