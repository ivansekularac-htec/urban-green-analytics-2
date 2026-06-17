"""
CRUD operations for sensor types.

This module provides functions for creating and retrieving
sensor type records from the database.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.helpers import commit_or_409
from app.models.sensors.sensor_type import SensorType
from app.schemas.sensors.sensor_type import SensorTypeCreate


def create(
    db: Session,
    payload: SensorTypeCreate,
) -> SensorType:
    """
    Create a new sensor type.

    Args:
        db: Active database session.
        payload: Sensor type data used to create the record.

    Returns:
        The newly created sensor type instance.
    """

    obj = SensorType(**payload.model_dump())

    db.add(obj)
    commit_or_409(db)
    db.refresh(obj)

    return obj


def get(
    db: Session,
    sensor_type_id: int,
) -> SensorType | None:
    """
    Retrieve a sensor type by its ID.

    Args:
        db: Active database session.
        sensor_type_id: Unique identifier of the sensor type.

    Returns:
        The sensor type instance if found, otherwise None.
    """

    return db.get(SensorType, sensor_type_id)


def get_all(
    db: Session,
) -> list[SensorType]:
    """
    Retrieve all sensor types.

    Args:
        db: Active database session.

    Returns:
        A list of all sensor type records.
    """

    return list(db.scalars(select(SensorType)).all())
