"""
Farm crop repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crops.farm_crop import FarmCrop
from app.repositories.base_repository import BaseRepository


class FarmCropRepository(BaseRepository[FarmCrop]):
    """
    Repository for FarmCrop database operations.
    """

    def __init__(self, db: Session):
        super().__init__(FarmCrop, db)

    def list_by_farm_ids(
        self, farm_ids: list[int], skip: int = 0, limit: int = 100
    ) -> list[FarmCrop]:
        statement = (
            select(self.model).where(self.model.farm_id.in_(farm_ids)).offset(skip).limit(limit)
        )

        return list(self.db.scalars(statement).all())
