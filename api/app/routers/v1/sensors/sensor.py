from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.sensors.sensor import SensorCreate, SensorResponse, SensorUpdate
from app.services.sensors import sensor as sensor_service

router = APIRouter(prefix="/sensors", tags=["sensors"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[SensorResponse])
def get_sensors(db: DbSession):
    """List all sensors."""
    return sensor_service.get_sensors(db)


@router.get("/{sensor_id}", response_model=SensorResponse)
def get_sensor(sensor_id: int, db: DbSession):
    """Retrieve a single sensor by ID."""
    sensor = sensor_service.get_sensor(db, sensor_id)
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
    return sensor


@router.post("/", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
def create_sensor(payload: SensorCreate, db: DbSession):
    """Create a new sensor."""
    return sensor_service.create_sensor(db, payload)


@router.put("/{sensor_id}", response_model=SensorResponse)
def update_sensor(sensor_id: int, payload: SensorUpdate, db: DbSession):
    """Update an existing sensor."""
    sensor = sensor_service.get_sensor(db, sensor_id)
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
    return sensor_service.update_sensor(db, sensor, payload)


@router.delete("/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sensor(sensor_id: int, db: DbSession):
    """Delete a sensor."""
    sensor = sensor_service.get_sensor(db, sensor_id)
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
    sensor_service.delete_sensor(db, sensor)
