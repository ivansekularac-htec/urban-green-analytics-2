from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models.users.role import Role
from app.models.users.user_roles import UserRole
from app.repositories.users.user import UserRepository
from app.schemas.users.user import UserCreate
from app.services.users.user import UserService

ADMIN_ROLE_NAME = "Admin"


def ensure_superuser() -> None:
    settings = get_settings()

    with SessionLocal() as db:
        admin_role = db.scalar(select(Role).where(Role.name == ADMIN_ROLE_NAME))

        if admin_role is None:
            print("Admin role not found.")
            return

        user_service = UserService(UserRepository(db))

        existing_user = user_service.get_by_email(settings.superuser_email)

        if existing_user:
            print("Superuser already exists.")
            return

        user = user_service.create(
            UserCreate(
                email=settings.superuser_email,
                password=settings.superuser_password,
                full_name=settings.superuser_full_name,
                is_active=True,
            )
        )

        db.add(
            UserRole(
                user_id=user.id,
                role_id=admin_role.id,
            )
        )

        db.commit()

        print(f"Superuser '{settings.superuser_email}' created successfully.")
