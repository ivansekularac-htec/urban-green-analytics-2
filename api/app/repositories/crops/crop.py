"""
Crop repository.
"""

from sqlalchemy.orm import Session

from app.models.crops.crop import Crop
from app.repositories.base_repository import BaseRepository


class CropRepository(BaseRepository[Crop]):
    """
    Repository for Crop database operations.
    """

    def __init__(self, db: Session):
        super().__init__(Crop, db)
