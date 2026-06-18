"""
User repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.users.user import User
from app.models.users.user_roles import UserRole
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User database operations.
    """

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(
        self,
        email: str,
    ) -> User | None:
        statement = select(User).where(User.email == email)

        return self.db.scalar(statement)

    def get_with_roles(
        self,
        user_id: int,
    ) -> User | None:
        """
        Get user with roles eagerly loaded.
        """
        statement = (
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.id == user_id)
        )

        return self.db.scalar(statement)
