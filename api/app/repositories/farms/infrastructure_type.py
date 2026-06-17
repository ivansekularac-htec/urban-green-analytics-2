"""
Infrastructure type repository.
"""

from sqlalchemy.orm import Session

from app.models.farms.infrastructure_type import InfrastructureType
from app.repositories.base_repository import BaseRepository


class InfrastructureTypeRepository(BaseRepository[InfrastructureType]):
    """
    Repository for InfrastructureType database operations.
    """

    def __init__(self, db: Session):
        super().__init__(InfrastructureType, db)
