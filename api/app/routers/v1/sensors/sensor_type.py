from typing import Annotated

from app.services.sensors import sensor_type as sensor_type_service
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.sensors.sensor_type import SensorTypeCreate, SensorTypeResponse, SensorTypeUpdate

router = APIRouter(prefix="/sensor-types", tags=["sensor-types"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[SensorTypeResponse])
def get_sensor_types(db: DbSession):
    """List all sensor types."""
    return sensor_type_service.get_sensor_types(db)


@router.get("/{sensor_type_id}", response_model=SensorTypeResponse)
def get_sensor_type(sensor_type_id: int, db: DbSession):
    """Retrieve a single sensor type by ID."""
    sensor_type = sensor_type_service.get_sensor_type(db, sensor_type_id)
    if not sensor_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor type not found")
    return sensor_type


@router.post("/", response_model=SensorTypeResponse, status_code=status.HTTP_201_CREATED)
def create_sensor_type(payload: SensorTypeCreate, db: DbSession):
    """Create a new sensor type."""
    return sensor_type_service.create_sensor_type(db, payload)


@router.put("/{sensor_type_id}", response_model=SensorTypeResponse)
def update_sensor_type(sensor_type_id: int, payload: SensorTypeUpdate, db: DbSession):
    """Update an existing sensor type."""
    sensor_type = sensor_type_service.get_sensor_type(db, sensor_type_id)
    if not sensor_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor type not found")
    return sensor_type_service.update_sensor_type(db, sensor_type, payload)


@router.delete("/{sensor_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sensor_type(sensor_type_id: int, db: DbSession):
    """Delete a sensor type."""
    sensor_type = sensor_type_service.get_sensor_type(db, sensor_type_id)
    if not sensor_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor type not found")
    sensor_type_service.delete_sensor_type(db, sensor_type)
