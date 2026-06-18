"""
Harvest service.
"""

from app.models.harvests.harvest import Harvest
from app.models.users.user import User
from app.repositories.harvests.harvest import HarvestRepository
from app.schemas.harvests.harvest import HarvestCreate, HarvestUpdate
from app.services.scoped_service import ScopedService


class HarvestService(ScopedService[Harvest, HarvestCreate, HarvestUpdate]):
    """
    Service for Harvest business logic.
    """

    def __init__(self, repository: HarvestRepository, current_user: User):
        super().__init__(repository, "Harvest", current_user)
