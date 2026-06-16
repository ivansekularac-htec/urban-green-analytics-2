"""
Growing system type repository.
"""

from sqlalchemy.orm import Session

from app.models.farms.growing_system_type import GrowingSystemType
from app.repositories.base_repository import BaseRepository


class GrowingSystemTypeRepository(BaseRepository[GrowingSystemType]):
    """
    Repository for GrowingSystemType database operations.
    """

    def __init__(self, db: Session):
        super().__init__(GrowingSystemType, db)
