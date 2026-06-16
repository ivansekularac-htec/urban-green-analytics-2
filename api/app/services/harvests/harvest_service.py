"""
harvest_service.py
Service functions for harvest CRUD operations.

This module contains database operations for creating, reading,
updating, and deleting Harvest records.
"""

from sqlalchemy.orm import Session

from app.models.harvests.harvest import Harvest
from app.schemas.harvests.harvest import HarvestCreate, HarvestUpdate


def create_harvest(
    db: Session,
    harvest_data: HarvestCreate,
) -> Harvest:
    """Create a new harvest."""
    harvest = Harvest(**harvest_data.model_dump())

    db.add(harvest)
    db.commit()
    db.refresh(harvest)

    return harvest


def get_harvests(
    db: Session,
) -> list[Harvest]:
    """Return all harvests."""
    return db.query(Harvest).all()


def get_harvest_by_id(
    db: Session,
    harvest_id: int,
) -> Harvest | None:
    """Return a harvest by ID."""
    return db.get(Harvest, harvest_id)


def update_harvest(
    db: Session,
    harvest: Harvest,
    harvest_data: HarvestUpdate,
) -> Harvest:
    """Update an existing harvest."""
    update_data = harvest_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(harvest, field, value)

    db.commit()
    db.refresh(harvest)

    return harvest


def delete_harvest(
    db: Session,
    harvest: Harvest,
) -> None:
    """Delete an existing harvest."""
    db.delete(harvest)
    db.commit()
