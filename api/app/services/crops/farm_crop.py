"""
Farm crop service.
"""

from app.models.crops.farm_crop import FarmCrop
from app.models.users.user import User
from app.repositories.crops.farm_crop import FarmCropRepository
from app.schemas.crops.farm_crop import FarmCropCreate, FarmCropUpdate
from app.services.scoped_service import ScopedService


class FarmCropService(ScopedService[FarmCrop, FarmCropCreate, FarmCropUpdate]):
    """
    Service for FarmCrop business logic.
    """

    def __init__(self, repository: FarmCropRepository, current_user: User):
        super().__init__(repository, "Farm crop", current_user)
