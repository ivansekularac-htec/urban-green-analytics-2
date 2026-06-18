"""
Role repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users.role import Role
from app.repositories.base_repository import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """
    Repository for Role database operations.
    """

    def __init__(self, db: Session):
        super().__init__(Role, db)

    def get_by_name(self, name: str) -> Role | None:
        """
        Get a role by its name.

        Args:
            name (str): The name of the role.

        Returns:
            Role | None: The Role object if found, otherwise None.
        """
        statement = select(Role).where(Role.name == name)
        return self.db.scalar(statement)
