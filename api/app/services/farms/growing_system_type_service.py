"""
Growing system type service.
"""

from app.models.farms.growing_system_type import GrowingSystemType
from app.repositories.farms.growing_system_type_repository import GrowingSystemTypeRepository
from app.schemas.farms.growing_system_type import (
    GrowingSystemTypeCreate,
    GrowingSystemTypeUpdate,
)
from app.services.base_service import BaseService


class GrowingSystemTypeService(
    BaseService[GrowingSystemType, GrowingSystemTypeCreate, GrowingSystemTypeUpdate]
):
    """
    Service for GrowingSystemType business logic.
    """

    def __init__(self, repository: GrowingSystemTypeRepository):
        super().__init__(repository, "Growing system type")
