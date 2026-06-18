"""
Farm service.
"""

from app.models.farms.farm import Farm
from app.models.users.user import User
from app.repositories.farms.farm import FarmRepository
from app.schemas.farms.farm import FarmCreate, FarmUpdate
from app.services.scoped_service import ScopedService


class FarmService(ScopedService[Farm, FarmCreate, FarmUpdate]):
    """
    Service for Farm business logic.

    The owning farm of a Farm entity is its own primary key.
    """

    farm_field = "id"

    def __init__(self, repository: FarmRepository, current_user: User):
        super().__init__(repository, "Farm", current_user)
