"""
CRUD operations for growing system types.

This module provides functions for creating and retrieving
growing system type records from the database.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.helpers import commit_or_409
from app.models.farms.growing_system_type import GrowingSystemType
from app.schemas.farms.growing_system_type import GrowingSystemTypeCreate


def create(
    db: Session,
    payload: GrowingSystemTypeCreate,
) -> GrowingSystemType:
    """
    Create a new growing system type.

    Args:
        db: Active database session.
        payload: Growing system type data used to create the record.

    Returns:
        The newly created growing system type instance.
    """

    obj = GrowingSystemType(**payload.model_dump())

    db.add(obj)
    commit_or_409(db)
    db.refresh(obj)

    return obj


def get(
    db: Session,
    growing_system_type_id: int,
) -> GrowingSystemType | None:
    """
    Retrieve a growing system type by its ID.

    Args:
        db: Active database session.
        growing_system_type_id: Unique identifier of the growing system type.

    Returns:
        The growing system type instance if found, otherwise None.
    """

    return db.get(GrowingSystemType, growing_system_type_id)


def get_all(
    db: Session,
) -> list[GrowingSystemType]:
    """
    Retrieve all growing system types.

    Args:
        db: Active database session.

    Returns:
        A list of all growing system type records.
    """

    return list(db.scalars(select(GrowingSystemType)).all())
