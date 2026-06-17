"""
Generic repository utilities for CRUD database operations.
"""

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository for common CRUD database operations.
    """

    def __init__(self, model: type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, item_id: int) -> ModelType | None:
        return self.db.get(self.model, item_id)

    def list(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        statement = select(self.model).offset(skip).limit(limit)
        return list(self.db.scalars(statement).all())

    def create(self, data: dict) -> ModelType:
        item = self.model(**data)
        self.db.add(item)
        self.db.flush()
        self.db.refresh(item)
        return item

    def update(self, item: ModelType, data: dict) -> ModelType:
        for field, value in data.items():
            setattr(item, field, value)

        self.db.flush()
        self.db.refresh(item)
        return item

    def delete(self, item: ModelType) -> None:
        self.db.delete(item)
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
