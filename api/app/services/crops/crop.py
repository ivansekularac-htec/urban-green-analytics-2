"""
Crop service.
"""

from app.models.crops.crop import Crop
from app.repositories.crops.crop import CropRepository
from app.schemas.crops.crop import CropCreate, CropUpdate
from app.services.base_service import BaseService


class CropService(BaseService[Crop, CropCreate, CropUpdate]):
    """
    Service for Crop business logic.
    """

    def __init__(self, repository: CropRepository):
        super().__init__(repository, "Crop")
