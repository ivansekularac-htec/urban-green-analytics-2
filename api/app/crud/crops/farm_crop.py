"""
CRUD operations for farm crop assignments.

This module provides functions for creating, retrieving,
updating, and deleting farm crop records in the database.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crops.farm_crop import FarmCrop
from app.schemas.crops.farm_crop import FarmCropCreate, FarmCropUpdate


def create(
    db: Session,
    payload: FarmCropCreate,
) -> FarmCrop:
    """
    Create a new farm crop assignment.

    Args:
        db: Active database session.
        payload: Farm crop data used to create the record.

    Returns:
        The newly created farm crop instance.
    """

    obj = FarmCrop(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    farm_crop_id: int,
) -> FarmCrop | None:
    """
    Retrieve a farm crop assignment by its ID.

    Args:
        db: Active database session.
        farm_crop_id: Unique identifier of the farm crop assignment.

    Returns:
        The farm crop instance if found, otherwise None.
    """

    return db.get(FarmCrop, farm_crop_id)


def get_all(
    db: Session,
) -> list[FarmCrop]:
    """
    Retrieve all farm crop assignments.

    Args:
        db: Active database session.

    Returns:
        A list of all farm crop records.
    """

    return list(db.scalars(select(FarmCrop)).all())


def update(
    db: Session,
    farm_crop: FarmCrop,
    payload: FarmCropUpdate,
) -> FarmCrop:
    """
    Update an existing farm crop assignment.

    Args:
        db: Active database session.
        farm_crop: Existing farm crop instance to update.
        payload: Data containing the fields to be updated.

    Returns:
        The updated farm crop instance.
    """

    for field, value in payload.model_dump(
        exclude_unset=True,
    ).items():
        setattr(farm_crop, field, value)

    db.commit()
    db.refresh(farm_crop)

    return farm_crop


def delete(
    db: Session,
    farm_crop: FarmCrop,
) -> None:
    """
    Delete an existing farm crop assignment.

    Args:
        db: Active database session.
        farm_crop: Farm crop instance to delete.

    Returns:
        None.
    """

    db.delete(farm_crop)
    db.commit()
