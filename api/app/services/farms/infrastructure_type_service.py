"""
farm_infrastructure_type_service.py
Service functions for farm infrastructure type CRUD operations.

This module contains database operations for creating, reading,
updating, and deleting FarmInfrastructureType records.
"""

from sqlalchemy.orm import Session

from app.models.farms.infrastructure_type import InfrastructureType
from app.schemas.farms.infrastructure_type import (
    InfrastructureTypeCreate,
    InfrastructureTypeUpdate,
)


def create_farm_infrastructure_type(
    db: Session,
    infrastructure_type_data: InfrastructureTypeCreate,
) -> InfrastructureType:
    """Create a new farm infrastructure type."""
    infrastructure_type = InfrastructureType(**infrastructure_type_data.model_dump())

    db.add(infrastructure_type)
    db.commit()
    db.refresh(infrastructure_type)

    return infrastructure_type


def get_farm_infrastructure_types(
    db: Session,
) -> list[InfrastructureType]:
    """Return all farm infrastructure types."""
    return db.query(InfrastructureType).all()


def get_farm_infrastructure_type_by_id(
    db: Session,
    infrastructure_type_id: int,
) -> InfrastructureType | None:
    """Return a farm infrastructure type by ID."""
    return db.get(InfrastructureType, infrastructure_type_id)


def update_farm_infrastructure_type(
    db: Session,
    infrastructure_type: InfrastructureType,
    infrastructure_type_data: InfrastructureTypeUpdate,
) -> InfrastructureType:
    """Update an existing farm infrastructure type."""
    update_data = infrastructure_type_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(infrastructure_type, field, value)

    db.commit()
    db.refresh(infrastructure_type)

    return infrastructure_type


def delete_farm_infrastructure_type(
    db: Session,
    infrastructure_type: InfrastructureType,
) -> None:
    """Delete an existing farm infrastructure type."""
    db.delete(infrastructure_type)
    db.commit()
