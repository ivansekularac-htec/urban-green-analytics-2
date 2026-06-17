"""
CRUD operations for crops.

This module provides functions for creating and retrieving
crop records from the database.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.helpers import commit_or_409
from app.models.crops.crop import Crop
from app.schemas.crops.crop import CropCreate


def create(
    db: Session,
    payload: CropCreate,
) -> Crop:
    """
    Create a new crop.

    Args:
        db: Active database session.
        payload: Crop data used to create the record.

    Returns:
        The newly created crop instance.
    """

    obj = Crop(**payload.model_dump())

    db.add(obj)
    commit_or_409(db)
    db.refresh(obj)

    return obj


def get(
    db: Session,
    crop_id: int,
) -> Crop | None:
    """
    Retrieve a crop by its ID.

    Args:
        db: Active database session.
        crop_id: Unique identifier of the crop.

    Returns:
        The crop instance if found, otherwise None.
    """

    return db.get(Crop, crop_id)


def get_all(
    db: Session,
) -> list[Crop]:
    """
    Retrieve all crops.

    Args:
        db: Active database session.

    Returns:
        A list of all crop records.
    """

    return list(db.scalars(select(Crop)).all())
