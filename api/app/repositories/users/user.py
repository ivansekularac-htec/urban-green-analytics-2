"""
User repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.users.role import Role
from app.models.users.user import User
from app.models.users.user_roles import UserRole
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User database operations.
    """

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.db.scalar(statement)

    def get_with_roles(self, user_id: int) -> User | None:
        statement = (
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.id == user_id)
        )
        return self.db.scalar(statement)

    def get_role_names_for_user(self, user_id: int) -> list[str]:
        statement = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id, UserRole.farm_id.is_(None))
        )
        return list(self.db.scalars(statement).all())

    def get_user_assignments(self, user_id: int) -> list[tuple[str, int | None]]:
        statement = (
            select(Role.name, UserRole.farm_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        return list(self.db.execute(statement).all())
