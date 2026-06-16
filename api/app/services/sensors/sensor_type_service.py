"""
sensor_type_service.py
Service functions for sensor type CRUD operations.

This module contains database operations for creating, reading,
updating, and deleting SensorType records.
"""

from sqlalchemy.orm import Session

from app.models.sensors.sensor_type import SensorType
from app.schemas.sensors.sensor_type import SensorTypeCreate, SensorTypeUpdate


def create_sensor_type(
    db: Session,
    sensor_type_data: SensorTypeCreate,
) -> SensorType:
    """Create a new sensor type."""
    sensor_type = SensorType(**sensor_type_data.model_dump())

    db.add(sensor_type)
    db.commit()
    db.refresh(sensor_type)

    return sensor_type


def get_sensor_types(
    db: Session,
) -> list[SensorType]:
    """Return all sensor types."""
    return db.query(SensorType).all()


def get_sensor_type_by_id(
    db: Session,
    sensor_type_id: int,
) -> SensorType | None:
    """Return a sensor type by ID."""
    return db.get(SensorType, sensor_type_id)


def update_sensor_type(
    db: Session,
    sensor_type: SensorType,
    sensor_type_data: SensorTypeUpdate,
) -> SensorType:
    """Update an existing sensor type."""
    update_data = sensor_type_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(sensor_type, field, value)

    db.commit()
    db.refresh(sensor_type)

    return sensor_type


def delete_sensor_type(
    db: Session,
    sensor_type: SensorType,
) -> None:
    """Delete an existing sensor type."""
    db.delete(sensor_type)
    db.commit()
