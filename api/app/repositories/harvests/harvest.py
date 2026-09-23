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

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        farm_ids: set[int] | None = None,
    ) -> list[Harvest]:
        statement = select(Harvest)
        if farm_ids is not None:
            if not farm_ids:
                return []
            statement = statement.where(Harvest.farm_id.in_(farm_ids))
        statement = statement.order_by(Harvest.id).offset(skip).limit(limit)
        return list(self.db.scalars(statement).all())
