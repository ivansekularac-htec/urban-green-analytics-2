"""
Farm repository.
"""

from sqlalchemy.orm import Session

from app.models.farms.farm import Farm
from app.repositories.base_repository import BaseRepository


class FarmRepository(BaseRepository[Farm]):
    """
    Repository for Farm database operations.
    """

    def __init__(self, db: Session):
        super().__init__(Farm, db)
