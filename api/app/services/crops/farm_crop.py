"""
Farm crop service.
"""

from app.models.crops.farm_crop import FarmCrop
from app.repositories.crops.farm_crop import FarmCropRepository
from app.schemas.crops.farm_crop import FarmCropCreate, FarmCropUpdate
from app.services.base_service import BaseService


class FarmCropService(BaseService[FarmCrop, FarmCropCreate, FarmCropUpdate]):
    """
    Service for FarmCrop business logic.
    """

    def __init__(self, repository: FarmCropRepository):
        super().__init__(repository, "Farm crop")

    def list_by_farm_ids(self, farm_ids: list[int], skip: int = 0, limit: int = 100):
        return self.repository.list_by_farm_ids(farm_ids, skip, limit)
