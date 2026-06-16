"""
farm_crop_service.py
Service functions for farm crop CRUD operations.

This module contains database operations for creating, reading,
updating, and deleting FarmCrop records.
"""

from sqlalchemy.orm import Session

from app.models.crops.farm_crop import FarmCrop
from app.schemas.crops.farm_crop import FarmCropCreate, FarmCropUpdate


def create_farm_crop(db: Session, farm_crop_data: FarmCropCreate) -> FarmCrop:
    """Create a new farm crop assignment."""
    farm_crop = FarmCrop(**farm_crop_data.model_dump())

    db.add(farm_crop)
    db.commit()
    db.refresh(farm_crop)

    return farm_crop


def get_farm_crops(db: Session) -> list[FarmCrop]:
    """Return all farm crop assignments."""
    return db.query(FarmCrop).all()


def update_farm_crop(
    db: Session,
    farm_crop: FarmCrop,
    farm_crop_data: FarmCropUpdate,
) -> FarmCrop:
    """Update an existing farm crop assignment."""
    update_data = farm_crop_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(farm_crop, field, value)

    db.commit()
    db.refresh(farm_crop)

    return farm_crop


def delete_farm_crop(db: Session, farm_crop: FarmCrop) -> None:
    """Delete an existing farm crop assignment."""
    db.delete(farm_crop)
    db.commit()
