"""
crop_category_service.py
Service functions for crop category CRUD operations.

This module contains database operations for creating, reading,
updating, and deleting CropCategory records.
"""

from sqlalchemy.orm import Session

from app.models.crops.crop_category import CropCategory
from app.schemas.crops.crop_category import (
    CropCategoryCreate,
    CropCategoryUpdate,
)


def create_crop_category(
    db: Session,
    crop_category_data: CropCategoryCreate,
) -> CropCategory:
    """Create a new crop category."""
    crop_category = CropCategory(**crop_category_data.model_dump())

    db.add(crop_category)
    db.commit()
    db.refresh(crop_category)

    return crop_category


def get_crop_categories(
    db: Session,
) -> list[CropCategory]:
    """Return all crop categories."""
    return db.query(CropCategory).all()


def get_crop_category_by_id(
    db: Session,
    crop_category_id: int,
) -> CropCategory | None:
    """Return a crop category by ID."""
    return db.get(CropCategory, crop_category_id)


def update_crop_category(
    db: Session,
    crop_category: CropCategory,
    crop_category_data: CropCategoryUpdate,
) -> CropCategory:
    """Update an existing crop category."""
    update_data = crop_category_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(crop_category, field, value)

    db.commit()
    db.refresh(crop_category)

    return crop_category


def delete_crop_category(
    db: Session,
    crop_category: CropCategory,
) -> None:
    """Delete an existing crop category."""
    db.delete(crop_category)
    db.commit()
