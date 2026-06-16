"""
CRUD operations for sensors.

This module provides functions for creating and retrieving
sensor records from the database.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sensors.sensor import Sensor
from app.schemas.sensors.sensor import SensorCreate


def create(
    db: Session,
    payload: SensorCreate,
) -> Sensor:
    """
    Create a new sensor.

    Args:
        db: Active database session.
        payload: Sensor data used to create the record.

    Returns:
        The newly created sensor instance.
    """

    obj = Sensor(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    sensor_id: int,
) -> Sensor | None:
    """
    Retrieve a sensor by its ID.

    Args:
        db: Active database session.
        sensor_id: Unique identifier of the sensor.

    Returns:
        The sensor instance if found, otherwise None.
    """

    return db.get(Sensor, sensor_id)


def get_all(
    db: Session,
) -> list[Sensor]:
    """
    Retrieve all sensors.

    Args:
        db: Active database session.

    Returns:
        A list of all sensor records.
    """

    return list(db.scalars(select(Sensor)).all())
