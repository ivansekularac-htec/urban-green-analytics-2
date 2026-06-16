from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sensors.sensor import Sensor
from app.schemas.sensors.sensor import SensorCreate


def create(
    db: Session,
    payload: SensorCreate,
) -> Sensor:

    obj = Sensor(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    sensor_id: int,
) -> Sensor | None:

    return db.get(Sensor, sensor_id)


def get_all(
    db: Session,
) -> list[Sensor]:

    return list(db.scalars(select(Sensor)).all())
