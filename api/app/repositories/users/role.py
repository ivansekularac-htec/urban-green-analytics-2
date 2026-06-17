"""
Role repository.
"""

from sqlalchemy.orm import Session

from app.models.users.role import Role
from app.repositories.base_repository import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """
    Repository for Role database operations.
    """

    def __init__(self, db: Session):
        super().__init__(Role, db)
