"""
User role repository.
"""

from sqlalchemy.orm import Session

from app.models.users.user_roles import UserRole
from app.repositories.base_repository import BaseRepository


class UserRoleRepository(BaseRepository[UserRole]):
    """
    Repository for UserRole database operations.
    """

    def __init__(self, db: Session):
        super().__init__(UserRole, db)
