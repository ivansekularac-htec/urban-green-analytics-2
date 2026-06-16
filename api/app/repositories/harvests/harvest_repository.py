"""
Harvest repository.
"""

from sqlalchemy.orm import Session

from app.models.harvests.harvest import Harvest
from app.repositories.base_repository import BaseRepository


class HarvestRepository(BaseRepository[Harvest]):
    """
    Repository for Harvest database operations.
    """

    def __init__(self, db: Session):
        super().__init__(Harvest, db)
