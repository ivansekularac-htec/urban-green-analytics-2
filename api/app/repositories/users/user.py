"""
user_repository.py
Repository for user-specific database queries.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users.role import Role
from app.models.users.user import User
from app.models.users.user_roles import UserRole
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User database operations."""

    def __init__(self, db: Session):
        """Initialize user repository."""
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        """Return a user by email address."""
        statement = select(User).where(User.email == email)

        return self.db.scalars(statement).first()

    def get_role_names(self, user_id: int) -> list[str]:
        """Return role names assigned to a user."""
        statement = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )

        return list(self.db.scalars(statement).all())
