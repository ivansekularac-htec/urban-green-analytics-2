"""
Service layer for FarmCrop entity.

Handles:
- linking crops to farms
- validating FK relations (farm_id, crop_id)
- tracking cultivation periods
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.crops.crop import Crop
from app.models.crops.farm_crop import FarmCrop
from app.models.farms.farm import Farm
from app.schemas.crops.farm_crop import FarmCropCreate, FarmCropUpdate


class FarmCropService:
    # ------------------------------------------------------
    # READ
    # ------------------------------------------------------
    def get(self, db: Session, farm_crop_id: int):
        """
        Get a single FarmCrop record by ID.
        """
        obj = db.query(FarmCrop).filter(FarmCrop.id == farm_crop_id).first()

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FarmCrop not found",
            )

        return obj

    def get_all(self, db: Session):
        """
        Get all FarmCrop records.
        """
        return db.query(FarmCrop).all()

    # ------------------------------------------------------
    # CREATE
    # ------------------------------------------------------
    def create(self, db: Session, data: FarmCropCreate):
        """
        Create a new FarmCrop record.

        Validates:
        - farm exists
        - crop exists
        """

        farm = db.query(Farm).filter(Farm.id == data.farm_id).first()
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found",
            )

        crop = db.query(Crop).filter(Crop.id == data.crop_id).first()
        if not crop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crop not found",
            )

        if data.ended_at is not None and data.ended_at < data.started_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ended_at cannot be earlier than started_at",
            )

        obj = FarmCrop(**data.model_dump())

        db.add(obj)
        db.commit()
        db.refresh(obj)

        return obj

    # ------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------
    def update(self, db: Session, farm_crop_id: int, data: FarmCropUpdate):
        """
        Update FarmCrop record ().
        """
        obj = self.get(db, farm_crop_id)

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FarmCrop not found",
            )

        update_data = data.model_dump(exclude_unset=True)

        # combine current + incoming values for validation
        started_at = update_data.get("started_at", obj.started_at)
        ended_at = update_data.get("ended_at", obj.ended_at)

        if ended_at is not None and ended_at < started_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ended_at cannot be earlier than started_at",
            )

        for key, value in update_data.items():
            setattr(obj, key, value)

        db.commit()
        db.refresh(obj)

        return obj

    # ------------------------------------------------------
    # DELETE
    # ------------------------------------------------------
    def delete(self, db: Session, farm_crop_id: int):
        """
        Delete FarmCrop record.
        """

        obj = self.get(db, farm_crop_id)

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FarmCrop not found",
            )

        db.delete(obj)
        db.commit()

        return None
