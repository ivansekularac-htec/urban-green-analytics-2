"""
CRUD operations for farms.

This module provides functions for creating, retrieving,
updating, and deleting farm records in the database.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.helpers import commit_or_409
from app.models.farms.farm import Farm
from app.schemas.farms.farm import FarmCreate, FarmUpdate


def create(
    db: Session,
    payload: FarmCreate,
) -> Farm:
    """
    Create a new farm.

    Args:
        db: Active database session.
        payload: Farm data used to create the record.

    Returns:
        The newly created farm instance.
    """

    obj = Farm(**payload.model_dump())

    db.add(obj)
    commit_or_409(db)
    db.refresh(obj)

    return obj


def get(
    db: Session,
    farm_id: int,
) -> Farm | None:
    """
    Retrieve a farm by its ID.

    Args:
        db: Active database session.
        farm_id: Unique identifier of the farm.

    Returns:
        The farm instance if found, otherwise None.
    """

    return db.get(Farm, farm_id)


def get_all(
    db: Session,
) -> list[Farm]:
    """
    Retrieve all farms.

    Args:
        db: Active database session.

    Returns:
        A list of all farm records.
    """

    return list(db.scalars(select(Farm)).all())


def update(
    db: Session,
    farm: Farm,
    payload: FarmUpdate,
) -> Farm:
    """
    Update an existing farm.

    Args:
        db: Active database session.
        farm: Existing farm instance to update.
        payload: Data containing the fields to be updated.

    Returns:
        The updated farm instance.
    """

    for field, value in payload.model_dump(
        exclude_unset=True,
    ).items():
        setattr(farm, field, value)

    commit_or_409(db)
    db.refresh(farm)

    return farm


def delete(
    db: Session,
    farm: Farm,
) -> None:
    """
    Delete an existing farm.

    Args:
        db: Active database session.
        farm: Farm instance to delete.

    Returns:
        None.
    """

    db.delete(farm)
    commit_or_409(db)
