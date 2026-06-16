"""
sensor_service.py
Service functions for sensor CRUD operations.

This module contains database operations for creating, reading,
updating, and deleting Sensor records.
"""

from sqlalchemy.orm import Session

from app.models.sensors.sensor import Sensor
from app.schemas.sensors.sensor import SensorCreate, SensorUpdate


def create_sensor(
    db: Session,
    sensor_data: SensorCreate,
) -> Sensor:
    """Create a new sensor."""
    sensor = Sensor(**sensor_data.model_dump())

    db.add(sensor)
    db.commit()
    db.refresh(sensor)

    return sensor


def get_sensors(
    db: Session,
) -> list[Sensor]:
    """Return all sensors."""
    return db.query(Sensor).all()


def get_sensor_by_id(
    db: Session,
    sensor_id: int,
) -> Sensor | None:
    """Return a sensor by ID."""
    return db.get(Sensor, sensor_id)


def update_sensor(
    db: Session,
    sensor: Sensor,
    sensor_data: SensorUpdate,
) -> Sensor:
    """Update an existing sensor."""
    update_data = sensor_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(sensor, field, value)

    db.commit()
    db.refresh(sensor)

    return sensor


def delete_sensor(
    db: Session,
    sensor: Sensor,
) -> None:
    """Delete an existing sensor."""
    db.delete(sensor)
    db.commit()
