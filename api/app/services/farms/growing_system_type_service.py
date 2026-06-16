"""
growing_system_type_service.py
Service functions for growing system type CRUD operations.

This module contains database operations for creating, reading,
updating, and deleting GrowingSystemType records.
"""

from sqlalchemy.orm import Session

from app.models.farms.growing_system_type import GrowingSystemType
from app.schemas.farms.growing_system_type import (
    GrowingSystemTypeCreate,
    GrowingSystemTypeUpdate,
)


def create_growing_system_type(
    db: Session,
    growing_system_type_data: GrowingSystemTypeCreate,
) -> GrowingSystemType:
    """Create a new growing system type."""
    growing_system_type = GrowingSystemType(**growing_system_type_data.model_dump())

    db.add(growing_system_type)
    db.commit()
    db.refresh(growing_system_type)

    return growing_system_type


def get_growing_system_types(
    db: Session,
) -> list[GrowingSystemType]:
    """Return all growing system types."""
    return db.query(GrowingSystemType).all()


def get_growing_system_type_by_id(
    db: Session,
    growing_system_type_id: int,
) -> GrowingSystemType | None:
    """Return a growing system type by ID."""
    return db.get(GrowingSystemType, growing_system_type_id)


def update_growing_system_type(
    db: Session,
    growing_system_type: GrowingSystemType,
    growing_system_type_data: GrowingSystemTypeUpdate,
) -> GrowingSystemType:
    """Update an existing growing system type."""
    update_data = growing_system_type_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(growing_system_type, field, value)

    db.commit()
    db.refresh(growing_system_type)

    return growing_system_type


def delete_growing_system_type(
    db: Session,
    growing_system_type: GrowingSystemType,
) -> None:
    """Delete an existing growing system type."""
    db.delete(growing_system_type)
    db.commit()
