"""
Harvest service.
"""

from app.models.harvests.harvest import Harvest
from app.repositories.harvests.harvest_repository import HarvestRepository
from app.schemas.harvests.harvest import HarvestCreate, HarvestUpdate
from app.services.base_service import BaseService


class HarvestService(BaseService[Harvest, HarvestCreate, HarvestUpdate]):
    """
    Service for Harvest business logic.
    """

    def __init__(self, repository: HarvestRepository):
        super().__init__(repository, "Harvest")
