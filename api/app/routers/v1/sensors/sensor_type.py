"""
sensor_types.py
API routes for sensor type management.

This module defines CRUD endpoints for SensorType resources.
"""

from fastapi import APIRouter, status

from app.database import SessionDep
from app.models.sensors.sensor_type import SensorType
from app.schemas.sensors.sensor_type import (
    SensorTypeCreate,
    SensorTypeResponse,
    SensorTypeUpdate,
)
from app.services.common import get_or_404
from app.services.sensors import sensor_type_service

router = APIRouter(
    prefix="/sensor-types",
    tags=["Sensor Types"],
)


@router.post(
    "",
    response_model=SensorTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sensor_type(
    sensor_type_data: SensorTypeCreate,
    db: SessionDep,
) -> SensorTypeResponse:
    """Create a new sensor type."""
    return sensor_type_service.create_sensor_type(
        db,
        sensor_type_data,
    )


@router.get(
    "",
    response_model=list[SensorTypeResponse],
)
def get_sensor_types(
    db: SessionDep,
) -> list[SensorTypeResponse]:
    """Return all sensor types."""
    return sensor_type_service.get_sensor_types(db)


@router.get(
    "/{sensor_type_id}",
    response_model=SensorTypeResponse,
)
def get_sensor_type(
    sensor_type_id: int,
    db: SessionDep,
) -> SensorTypeResponse:
    """Return a sensor type by ID."""
    return get_or_404(
        db,
        SensorType,
        sensor_type_id,
        "Sensor type",
    )


@router.put(
    "/{sensor_type_id}",
    response_model=SensorTypeResponse,
)
def update_sensor_type(
    sensor_type_id: int,
    sensor_type_data: SensorTypeUpdate,
    db: SessionDep,
) -> SensorTypeResponse:
    """Update a sensor type by ID."""
    sensor_type = get_or_404(
        db,
        SensorType,
        sensor_type_id,
        "Sensor type",
    )

    return sensor_type_service.update_sensor_type(
        db,
        sensor_type,
        sensor_type_data,
    )


@router.delete(
    "/{sensor_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_sensor_type(
    sensor_type_id: int,
    db: SessionDep,
) -> None:
    """Delete a sensor type by ID."""
    sensor_type = get_or_404(
        db,
        SensorType,
        sensor_type_id,
        "Sensor type",
    )

    sensor_type_service.delete_sensor_type(
        db,
        sensor_type,
    )
