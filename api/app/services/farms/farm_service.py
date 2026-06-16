"""
farm_service.py
Service functions for farm CRUD operations.

This module contains database operations for creating, reading,
updating, and deleting Farm records.
"""

from sqlalchemy.orm import Session

from app.models.farms.farm import Farm
from app.schemas.farms.farm import FarmCreate, FarmUpdate


def create_farm(db: Session, farm_data: FarmCreate) -> Farm:
    """Create a new farm."""
    farm = Farm(**farm_data.model_dump())

    db.add(farm)
    db.commit()
    db.refresh(farm)

    return farm


def get_farms(db: Session) -> list[Farm]:
    """Return all farms."""
    return db.query(Farm).all()


def get_farm_by_id(db: Session, farm_id: int) -> Farm | None:
    """Return a farm by ID."""
    return db.get(Farm, farm_id)


def update_farm(
    db: Session,
    farm: Farm,
    farm_data: FarmUpdate,
) -> Farm:
    """Update an existing farm."""
    update_data = farm_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(farm, field, value)

    db.commit()
    db.refresh(farm)

    return farm


def delete_farm(db: Session, farm: Farm) -> None:
    """Delete an existing farm."""
    db.delete(farm)
    db.commit()
