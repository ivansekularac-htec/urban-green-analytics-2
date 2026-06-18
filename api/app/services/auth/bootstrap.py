"""
Authentication bootstrap utilities.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users.role import Role
from app.models.users.user import User
from app.models.users.user_roles import UserRole
from app.security.password import hash_password

logger = logging.getLogger(__name__)


def ensure_superuser(db: Session, email: str, password: str) -> None:
    """
    Ensure that a superuser exists and has the admin role.
    """
    user = db.scalar(select(User).where(User.email == email))

    if user is None:
        user = User(
            email=email,
            full_name="System Administrator",
            password_hash=hash_password(password),
            is_active=True,
        )
        db.add(user)
        db.flush()

    admin_role = db.scalar(select(Role).where(Role.name.ilike("admin")))

    if admin_role is None:
        logger.warning("Admin role does not exist. Superuser role was not assigned.")
        db.commit()
        return

    existing_user_role = db.scalar(
        select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.role_id == admin_role.id,
            UserRole.farm_id.is_(None),
        )
    )

    if existing_user_role is None:
        db.add(
            UserRole(
                user_id=user.id,
                role_id=admin_role.id,
                farm_id=None,
            )
        )

    db.commit()
    logger.info("Superuser ensured successfully.")
