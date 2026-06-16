"""
sensors.py
API routes for sensor management.

This module defines CRUD endpoints for Sensor resources.
"""

from fastapi import APIRouter, status

from app.database import SessionDep
from app.models.farms.farm import Farm
from app.models.sensors.sensor import Sensor
from app.models.sensors.sensor_type import SensorType
from app.schemas.sensors.sensor import (
    SensorCreate,
    SensorResponse,
    SensorUpdate,
)
from app.services.common import get_or_404
from app.services.sensors import sensor_service

router = APIRouter(
    prefix="/sensors",
    tags=["Sensors"],
)


@router.post(
    "",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sensor(
    sensor_data: SensorCreate,
    db: SessionDep,
) -> SensorResponse:
    """Create a new sensor."""
    get_or_404(
        db,
        Farm,
        sensor_data.farm_id,
        "Farm",
    )

    get_or_404(
        db,
        SensorType,
        sensor_data.sensor_type_id,
        "Sensor type",
    )

    return sensor_service.create_sensor(
        db,
        sensor_data,
    )


@router.get(
    "",
    response_model=list[SensorResponse],
)
def get_sensors(
    db: SessionDep,
) -> list[SensorResponse]:
    """Return all sensors."""
    return sensor_service.get_sensors(db)


@router.get(
    "/{sensor_id}",
    response_model=SensorResponse,
)
def get_sensor(
    sensor_id: int,
    db: SessionDep,
) -> SensorResponse:
    """Return a sensor by ID."""
    return get_or_404(
        db,
        Sensor,
        sensor_id,
        "Sensor",
    )


@router.put(
    "/{sensor_id}",
    response_model=SensorResponse,
)
def update_sensor(
    sensor_id: int,
    sensor_data: SensorUpdate,
    db: SessionDep,
) -> SensorResponse:
    """Update a sensor by ID."""
    sensor = get_or_404(
        db,
        Sensor,
        sensor_id,
        "Sensor",
    )

    if sensor_data.farm_id is not None:
        get_or_404(
            db,
            Farm,
            sensor_data.farm_id,
            "Farm",
        )

    if sensor_data.sensor_type_id is not None:
        get_or_404(
            db,
            SensorType,
            sensor_data.sensor_type_id,
            "Sensor type",
        )

    return sensor_service.update_sensor(
        db,
        sensor,
        sensor_data,
    )


@router.delete(
    "/{sensor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_sensor(
    sensor_id: int,
    db: SessionDep,
) -> None:
    """Delete a sensor by ID."""
    sensor = get_or_404(
        db,
        Sensor,
        sensor_id,
        "Sensor",
    )

    sensor_service.delete_sensor(
        db,
        sensor,
    )
