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

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        farm_ids: set[int] | None = None,
    ) -> list[Farm]:
        """List farms, restricting to ``farm_ids`` when provided.

        Farms are filtered by their own ``id`` column rather than the
        ``farm_id`` convention used on child entities.
        """
        statement = select(Farm)
        if farm_ids is not None:
            if not farm_ids:
                return []
            statement = statement.where(Farm.id.in_(farm_ids))
        statement = statement.offset(skip).limit(limit)
        return list(self.db.scalars(statement).all())
