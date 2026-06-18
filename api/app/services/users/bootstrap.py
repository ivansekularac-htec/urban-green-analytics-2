"""Bootstrap the initial superuser (Admin)."""

import logging

from sqlalchemy.orm import Session

from app.config import Settings
from app.repositories.users.role import RoleRepository
from app.repositories.users.user import UserRepository
from app.repositories.users.user_role import UserRoleRepository
from app.schemas.users.user import UserCreate
from app.security.roles import RoleName
from app.services.users.user import UserService

logger = logging.getLogger(__name__)


def ensure_superuser(db: Session, settings: Settings) -> None:
    """
    Create the initial Admin user if configured and not already present.

    Idempotent: safe to run on every startup.
    """
    if not settings.superuser_email or not settings.superuser_password:
        logger.warning("Superuser env vars not set; skipping bootstrap.")
        return

    user_repository = UserRepository(db)
    existing = user_repository.get_by_email(settings.superuser_email)
    if existing is not None:
        logger.info("Superuser already exists; skipping bootstrap.")
        return

    user_service = UserService(user_repository)
    user = user_service.create(
        UserCreate(
            email=settings.superuser_email,
            full_name=settings.superuser_full_name,
            password=settings.superuser_password,
            is_active=True,
        )
    )

    role_repository = RoleRepository(db)
    admin_role = role_repository.get_by_name(RoleName.ADMIN)
    if admin_role is None:
        raise RuntimeError(f"Role '{RoleName.ADMIN}' not found. Run database seed first.")

    user_role_repository = UserRoleRepository(db)
    user_role_repository.create(
        {
            "user_id": user.id,
            "role_id": admin_role.id,
            "farm_id": None,
        }
    )
    user_role_repository.commit()

    logger.info("Superuser '%s' created.", settings.superuser_email)
