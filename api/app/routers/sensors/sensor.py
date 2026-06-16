"""
API routes for Sensor management.
"""

from fastapi import APIRouter, Response, status

from app.database import DbSession
from app.schemas.sensors.sensor import (
    SensorCreate,
    SensorResponse,
    SensorUpdate,
)
from app.services.sensors.sensor import SensorService

sensor_router = APIRouter(
    prefix="/sensors",
    tags=["Sensors"],
)

sensor_service = SensorService()


@sensor_router.get("", response_model=list[SensorResponse])
def get_sensors(db: DbSession):
    """
    Retrieve all sensors.
    """
    return sensor_service.get_all(db)


@sensor_router.get("/{sensor_id}", response_model=SensorResponse)
def get_sensor(
    sensor_id: int,
    db: DbSession,
):
    """
    Retrieve sensor by ID.
    """
    return sensor_service.get(db, sensor_id)


@sensor_router.post("", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
def create_sensor(
    data: SensorCreate,
    db: DbSession,
):
    """
    Create a new sensor.
    """
    return sensor_service.create(db, data)


@sensor_router.put("/{sensor_id}", response_model=SensorResponse)
def update_sensor(
    sensor_id: int,
    data: SensorUpdate,
    db: DbSession,
):
    """
    Update an existing sensor.
    """
    return sensor_service.update(
        db,
        sensor_id,
        data,
    )


@sensor_router.delete("/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sensor(
    sensor_id: int,
    db: DbSession,
):
    """
    Delete a sensor.
    """

    sensor_service.delete(
        db,
        sensor_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
