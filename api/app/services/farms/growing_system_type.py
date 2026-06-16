"""
Service layer for GrowingSystemType.

Handles business logic and DB operations:
- create
- read
- update
- delete
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.farms.growing_system_type import GrowingSystemType
from app.schemas.farms.growing_system_type import (
    GrowingSystemTypeCreate,
    GrowingSystemTypeUpdate,
)


class GrowingSystemTypeService:
    # -------------------------------------------------
    # READ
    # -------------------------------------------------
    def get(self, db: Session, type_id: int):
        """
        Retrieve a GrowingSystemType by its ID.
        """
        obj = db.query(GrowingSystemType).filter(GrowingSystemType.id == type_id).first()

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Growing system type not found",
            )

        return obj

    def get_all(self, db: Session):
        """
        Retrieve all GrowingSystemTypes.
        """
        return db.query(GrowingSystemType).all()

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------
    def create(self, db: Session, data: GrowingSystemTypeCreate):
        """
        Create a new GrowingSystemType.
        """
        existing = db.query(GrowingSystemType).filter(GrowingSystemType.name == data.name).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Growing system type with this name already exists",
            )

        obj = GrowingSystemType(**data.model_dump())

        db.add(obj)
        db.commit()
        db.refresh(obj)

        return obj

    # -------------------------------------------------
    # UPDATE
    # -------------------------------------------------
    def update(self, db: Session, type_id: int, data: GrowingSystemTypeUpdate):
        """
        Update an existing GrowingSystemType.
        """
        obj = self.get(db, type_id)

        update_data = data.model_dump(exclude_unset=True)

        for k, v in update_data.items():
            setattr(obj, k, v)

        db.commit()
        db.refresh(obj)

        return obj

    # -------------------------------------------------
    # DELETE
    # -------------------------------------------------
    def delete(self, db: Session, type_id: int):
        """
        Delete a GrowingSystemType by its ID.
        """

        obj = self.get(db, type_id)

        db.delete(obj)
        db.commit()

        return None
