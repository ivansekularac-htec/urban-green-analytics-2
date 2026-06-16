"""
Infrastructure type service.
"""

from app.models.farms.infrastructure_type import InfrastructureType
from app.repositories.farms.infrastructure_type_repository import InfrastructureTypeRepository
from app.schemas.farms.infrastructure_type import (
    InfrastructureTypeCreate,
    InfrastructureTypeUpdate,
)
from app.services.base_service import BaseService


class InfrastructureTypeService(
    BaseService[InfrastructureType, InfrastructureTypeCreate, InfrastructureTypeUpdate]
):
    """
    Service for InfrastructureType business logic.
    """

    def __init__(self, repository: InfrastructureTypeRepository):
        super().__init__(repository, "Infrastructure type")
