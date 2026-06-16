from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Sensor
from app.schemas import SensorCreate, SensorResponse, SensorUpdate

sensor_router = APIRouter(
    prefix="/sensors",
    tags=["Sensors"],
)


@sensor_router.get(
    "/",
    response_model=list[SensorResponse],
)
def get_sensors(
    db: Session = Depends(get_db),
):
    return db.query(Sensor).all()


@sensor_router.post(
    "/",
    response_model=SensorResponse,
    status_code=201,
)
def create_sensor(
    sensor_data: SensorCreate,
    db: Session = Depends(get_db),
):
    sensor = Sensor(
        **sensor_data.model_dump(),
    )

    db.add(sensor)
    db.commit()
    db.refresh(sensor)

    return sensor


@sensor_router.put(
    "/{sensor_id}",
    response_model=SensorResponse,
)
def update_sensor(
    sensor_id: int,
    sensor_data: SensorUpdate,
    db: Session = Depends(get_db),
):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()

    if sensor is None:
        raise HTTPException(
            status_code=404,
            detail="Sensor not found",
        )

    for field, value in sensor_data.model_dump(
        exclude_unset=True,
    ).items():
        setattr(sensor, field, value)

    db.commit()
    db.refresh(sensor)

    return sensor
