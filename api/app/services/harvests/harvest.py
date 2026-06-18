"""
Harvest service.
"""

from app.models.harvests.harvest import Harvest
from app.repositories.harvests.harvest import HarvestRepository
from app.schemas.harvests.harvest import HarvestCreate, HarvestUpdate
from app.services.base_service import BaseService


class HarvestService(BaseService[Harvest, HarvestCreate, HarvestUpdate]):
    """
    Service for Harvest business logic.
    """

    def __init__(self, repository: HarvestRepository):
        super().__init__(repository, "Harvest")

    def list_by_farm_ids(
        self, farm_ids: list[int], skip: int = 0, limit: int = 100
    ) -> list[Harvest]:
        return self.repository.list_by_farm(farm_ids, skip=skip, limit=limit)
