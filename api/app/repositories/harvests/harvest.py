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

    def list_by_farm_ids(
        self,
        farm_ids: list[int],
        skip: int = 0,
        limit: int = 100,
    ) -> list[Harvest]:
        """Return harvests that belong to the provided farm IDs."""
        if not farm_ids:
            return []

        statement = select(Harvest).where(Harvest.farm_id.in_(farm_ids)).offset(skip).limit(limit)

        return list(self.db.scalars(statement).all())
