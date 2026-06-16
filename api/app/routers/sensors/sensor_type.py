"""
API routes for SensorType management.
"""

from fastapi import APIRouter, Response, status

from app.database import DbSession
from app.schemas.sensors.sensor_type import (
    SensorTypeCreate,
    SensorTypeResponse,
    SensorTypeUpdate,
)
from app.services.sensors.sensor_type import SensorTypeService

sensor_type_router = APIRouter(
    prefix="/sensor-types",
    tags=["Sensor Types"],
)

sensor_type_service = SensorTypeService()


@sensor_type_router.get("", response_model=list[SensorTypeResponse])
def get_sensor_types(db: DbSession):
    """
    Retrieve all sensor types.
    """

    return sensor_type_service.get_all(db)


@sensor_type_router.get("/{sensor_type_id}", response_model=SensorTypeResponse)
def get_sensor_type(
    sensor_type_id: int,
    db: DbSession,
):
    """
    Retrieve a sensor type by ID.
    """

    return sensor_type_service.get(
        db,
        sensor_type_id,
    )


@sensor_type_router.post("", response_model=SensorTypeResponse, status_code=status.HTTP_201_CREATED)
def create_sensor_type(
    data: SensorTypeCreate,
    db: DbSession,
):
    """
    Create a new sensor type.
    """

    return sensor_type_service.create(
        db,
        data,
    )


@sensor_type_router.put("/{sensor_type_id}", response_model=SensorTypeResponse)
def update_sensor_type(
    sensor_type_id: int,
    data: SensorTypeUpdate,
    db: DbSession,
):
    """
    Update an existing sensor type.
    """

    return sensor_type_service.update(
        db,
        sensor_type_id,
        data,
    )


@sensor_type_router.delete("/{sensor_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sensor_type(
    sensor_type_id: int,
    db: DbSession,
):
    """
    Delete a sensor type.
    """

    sensor_type_service.delete(
        db,
        sensor_type_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
