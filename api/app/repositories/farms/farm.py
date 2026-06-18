"""
Farm repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.farms.farm import Farm
from app.repositories.base_repository import BaseRepository


class FarmRepository(BaseRepository[Farm]):
    """
    Repository for Farm database operations.
    """

    def __init__(self, db: Session):
        super().__init__(Farm, db)

    def list_by_ids(self, farm_ids: list[int], skip: int = 0, limit: int = 100):
        statement = select(self.model).where(self.model.id.in_(farm_ids)).offset(skip).limit(limit)
        return list(self.db.scalars(statement).all())
