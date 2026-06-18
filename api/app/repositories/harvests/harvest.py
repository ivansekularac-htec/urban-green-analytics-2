"""
Harvest repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.harvests.harvest import Harvest
from app.repositories.base_repository import BaseRepository


class HarvestRepository(BaseRepository[Harvest]):
    """
    Repository for Harvest database operations.
    """

    def __init__(self, db: Session):
        super().__init__(Harvest, db)

    def list_by_farm(self, farm_ids: list[int], skip: int = 0, limit: int = 100) -> list[Harvest]:
        statement = (
            select(self.model).where(self.model.farm_id.in_(farm_ids)).offset(skip).limit(limit)
        )
        return list(self.db.scalars(statement).all())
