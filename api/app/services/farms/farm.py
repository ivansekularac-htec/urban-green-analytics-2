"""
Farm service.
"""

from app.models.farms.farm import Farm
from app.repositories.farms.farm import FarmRepository
from app.schemas.farms.farm import FarmCreate, FarmUpdate
from app.services.base_service import BaseService


class FarmService(BaseService[Farm, FarmCreate, FarmUpdate]):
    """
    Service for Farm business logic.
    """

    def __init__(self, repository: FarmRepository):
        super().__init__(repository, "Farm")

    def list_by_ids(self, farm_ids: list[int], skip: int = 0, limit: int = 100):
        return self.repository.list_by_ids(farm_ids, skip, limit)
