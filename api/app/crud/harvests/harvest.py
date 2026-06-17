"""
CRUD operations for harvests.

This module provides functions for creating, retrieving,
updating, and deleting harvest records in the database.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.helpers import commit_or_409
from app.models.harvests.harvest import Harvest
from app.schemas.harvests.harvest import HarvestCreate, HarvestUpdate


def create(
    db: Session,
    payload: HarvestCreate,
) -> Harvest:
    """
    Create a new harvest.

    Args:
        db: Active database session.
        payload: Harvest data used to create the record.

    Returns:
        The newly created harvest instance.
    """

    obj = Harvest(**payload.model_dump())

    db.add(obj)
    commit_or_409(db)
    db.refresh(obj)

    return obj


def get(
    db: Session,
    harvest_id: int,
) -> Harvest | None:
    """
    Retrieve a harvest by its ID.

    Args:
        db: Active database session.
        harvest_id: Unique identifier of the harvest.

    Returns:
        The harvest instance if found, otherwise None.
    """

    return db.get(Harvest, harvest_id)


def get_all(
    db: Session,
) -> list[Harvest]:
    """
    Retrieve all harvests.

    Args:
        db: Active database session.

    Returns:
        A list of all harvest records.
    """

    return list(db.scalars(select(Harvest)).all())


def update(
    db: Session,
    harvest: Harvest,
    payload: HarvestUpdate,
) -> Harvest:
    """
    Update an existing harvest.

    Args:
        db: Active database session.
        harvest: Existing harvest instance to update.
        payload: Data containing the fields to be updated.

    Returns:
        The updated harvest instance.
    """

    for field, value in payload.model_dump(
        exclude_unset=True,
    ).items():
        setattr(harvest, field, value)

    commit_or_409(db)
    db.refresh(harvest)

    return harvest


def delete(
    db: Session,
    harvest: Harvest,
) -> None:
    """
    Delete an existing harvest.

    Args:
        db: Active database session.
        harvest: Harvest instance to delete.

    Returns:
        None.
    """

    db.delete(harvest)
    commit_or_409(db)
