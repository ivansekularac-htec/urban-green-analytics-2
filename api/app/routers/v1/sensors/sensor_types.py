from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.database import DbSession
from app.models.sensors.sensor_type import SensorType
from app.schemas.sensors.sensor_type import (
    SensorTypeCreate,
    SensorTypeResponse,
    SensorTypeUpdate,
)

sensor_types_router = APIRouter(prefix="/sensor-types", tags=["sensor-types"])


@sensor_types_router.post(
    "/",
    response_model=SensorTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sensor_type(
    payload: SensorTypeCreate,
    db: DbSession,
) -> SensorType:
    sensor_type = SensorType(**payload.model_dump())

    db.add(sensor_type)
    db.commit()
    db.refresh(sensor_type)

    return sensor_type


@sensor_types_router.get(
    "/",
    response_model=list[SensorTypeResponse],
)
def get_sensor_types(
    db: DbSession,
) -> list[SensorType]:
    return db.scalars(select(SensorType)).all()


@sensor_types_router.get(
    "/{sensor_type_id}",
    response_model=SensorTypeResponse,
)
def get_sensor_type(
    sensor_type_id: int,
    db: DbSession,
) -> SensorType:
    sensor_type = db.scalar(select(SensorType).where(SensorType.id == sensor_type_id))

    if sensor_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor type not found",
        )

    return sensor_type


@sensor_types_router.put(
    "/{sensor_type_id}",
    response_model=SensorTypeResponse,
)
def update_sensor_type(
    sensor_type_id: int,
    payload: SensorTypeUpdate,
    db: DbSession,
) -> SensorType:
    sensor_type = db.scalar(select(SensorType).where(SensorType.id == sensor_type_id))

    if sensor_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor type not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(sensor_type, field, value)

    db.commit()

    return sensor_type


@sensor_types_router.delete(
    "/{sensor_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_sensor_type(
    sensor_type_id: int,
    db: DbSession,
) -> None:
    sensor_type = db.scalar(select(SensorType).where(SensorType.id == sensor_type_id))

    if sensor_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor type not found",
        )

    db.delete(sensor_type)
    db.commit()
