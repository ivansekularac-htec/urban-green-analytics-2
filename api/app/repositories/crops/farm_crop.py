"""
Farm crop repository.
"""

from sqlalchemy.orm import Session

from app.models.crops.farm_crop import FarmCrop
from app.repositories.base_repository import BaseRepository


class FarmCropRepository(BaseRepository[FarmCrop]):
    """
    Repository for FarmCrop database operations.
    """

    def __init__(self, db: Session):
        super().__init__(FarmCrop, db)
