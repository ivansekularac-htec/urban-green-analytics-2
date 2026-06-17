"""
User repository.
"""

from sqlalchemy.orm import Session

from app.models.users.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User database operations.
    """

    def __init__(self, db: Session):
        super().__init__(User, db)
