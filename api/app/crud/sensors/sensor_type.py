from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sensors.sensor_type import SensorType
from app.schemas.sensors.sensor_type import SensorTypeCreate


def create(
    db: Session,
    payload: SensorTypeCreate,
) -> SensorType:

    obj = SensorType(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    sensor_type_id: int,
) -> SensorType | None:

    return db.get(SensorType, sensor_type_id)


def get_all(
    db: Session,
) -> list[SensorType]:

    return list(db.scalars(select(SensorType)).all())
