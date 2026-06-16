from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.database import DbSession
from app.models.sensors.sensor import Sensor
from app.schemas.sensors.sensor import (
    SensorCreate,
    SensorResponse,
    SensorUpdate,
)

sensors_router = APIRouter(prefix="/sensors", tags=["sensors"])


@sensors_router.post(
    "/",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sensor(
    payload: SensorCreate,
    db: DbSession,
) -> Sensor:
    sensor = Sensor(**payload.model_dump())

    db.add(sensor)
    db.commit()
    db.refresh(sensor)

    return sensor


@sensors_router.get(
    "/",
    response_model=list[SensorResponse],
)
def get_sensors(
    db: DbSession,
) -> list[Sensor]:
    return db.scalars(select(Sensor)).all()


@sensors_router.get(
    "/{sensor_id}",
    response_model=SensorResponse,
)
def get_sensor(
    sensor_id: int,
    db: DbSession,
) -> Sensor:
    sensor = db.scalar(select(Sensor).where(Sensor.id == sensor_id))

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    return sensor


@sensors_router.put(
    "/{sensor_id}",
    response_model=SensorResponse,
)
def update_sensor(
    sensor_id: int,
    payload: SensorUpdate,
    db: DbSession,
) -> Sensor:
    sensor = db.scalar(select(Sensor).where(Sensor.id == sensor_id))

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(sensor, field, value)

    db.commit()

    return sensor


@sensors_router.delete(
    "/{sensor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_sensor(
    sensor_id: int,
    db: DbSession,
) -> None:
    sensor = db.scalar(select(Sensor).where(Sensor.id == sensor_id))

    if sensor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sensor not found",
        )

    db.delete(sensor)
    db.commit()
