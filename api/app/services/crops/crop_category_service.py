"""
Crop category service.
"""

from app.models.crops.crop_category import CropCategory
from app.repositories.crops.crop_category_repository import CropCategoryRepository
from app.schemas.crops.crop_category import CropCategoryCreate, CropCategoryUpdate
from app.services.base_service import BaseService


class CropCategoryService(BaseService[CropCategory, CropCategoryCreate, CropCategoryUpdate]):
    """
    Service for CropCategory business logic.
    """

    def __init__(self, repository: CropCategoryRepository):
        super().__init__(repository, "Crop category")
