"""
Crop category repository.
"""

from sqlalchemy.orm import Session

from app.models.crops.crop_category import CropCategory
from app.repositories.base_repository import BaseRepository


class CropCategoryRepository(BaseRepository[CropCategory]):
    """
    Repository for CropCategory database operations.
    """

    def __init__(self, db: Session):
        super().__init__(CropCategory, db)
