"""
Service layer for Crop entity.

Handles business logic for:
- CRUD operations
- validation (category existence, uniqueness rules if needed)
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.crops.crop import Crop
from app.models.crops.crop_category import CropCategory
from app.schemas.crops.crop import CropCreate, CropUpdate


class CropService:
    # ------------------------------------------------------
    # READ
    # ------------------------------------------------------
    # def get(self, db: Session, crop_id: int):
    #     """
    #     Get a single crop by ID.
    #     """
    #     return db.query(Crop).filter(Crop.id == crop_id).first()

    def get(self, db: Session, crop_id: int):
        """
        Get a single crop by ID.
        """
        obj = db.query(Crop).filter(Crop.id == crop_id).first()

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crop not found",
            )

        return obj

    def get_all(self, db: Session):
        """
        Get all crops.
        """
        return db.query(Crop).all()

    # ------------------------------------------------------
    # CREATE
    # ------------------------------------------------------
    def create(self, db: Session, data: CropCreate):
        """
        Create a new crop.

        Validates that category exists before creation.
        """

        category = db.query(CropCategory).filter(CropCategory.id == data.category_id).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crop category not found",
            )

        obj = Crop(**data.model_dump())

        db.add(obj)
        db.commit()
        db.refresh(obj)

        return obj

    # ------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------
    def update(self, db: Session, crop_id: int, data: CropUpdate):
        """
        Update crop fields.
        """

        obj = self.get(db, crop_id)

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crop not found",
            )

        update_data = data.model_dump(exclude_unset=True)

        # validate category if changing
        if "category_id" in update_data:
            category = (
                db.query(CropCategory).filter(CropCategory.id == update_data["category_id"]).first()
            )

            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Crop category not found",
                )

        for key, value in update_data.items():
            setattr(obj, key, value)

        db.commit()
        db.refresh(obj)

        return obj

    # ------------------------------------------------------
    # DELETE
    # ------------------------------------------------------
    def delete(self, db: Session, crop_id: int):
        """
        Delete a crop by ID.
        """

        obj = self.get(db, crop_id)

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crop not found",
            )

        db.delete(obj)
        db.commit()

        return None
