"""
crop_service.py
Service functions for crop CRUD operations.

This module contains database operations for creating, reading,
updating, and deleting Crop records.
"""

from sqlalchemy.orm import Session

from app.models.crops.crop import Crop
from app.schemas.crops.crop import CropCreate, CropUpdate


def create_crop(db: Session, crop_data: CropCreate) -> Crop:
    """Create a new crop."""
    crop = Crop(**crop_data.model_dump())

    db.add(crop)
    db.commit()
    db.refresh(crop)

    return crop


def get_crops(db: Session) -> list[Crop]:
    """Return all crops."""
    return db.query(Crop).all()


def get_crop_by_id(db: Session, crop_id: int) -> Crop | None:
    """Return a crop by ID."""
    return db.get(Crop, crop_id)


def update_crop(
    db: Session,
    crop: Crop,
    crop_data: CropUpdate,
) -> Crop:
    """Update an existing crop."""
    update_data = crop_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(crop, field, value)

    db.commit()
    db.refresh(crop)

    return crop


def delete_crop(db: Session, crop: Crop) -> None:
    """Delete an existing crop."""
    db.delete(crop)
    db.commit()
