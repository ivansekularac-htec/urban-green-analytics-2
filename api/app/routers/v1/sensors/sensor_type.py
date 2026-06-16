from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SensorType
from app.schemas import SensorTypeCreate, SensorTypeResponse

sensor_type_router = APIRouter(
    prefix="/sensor-types",
    tags=["Sensor Types"],
)


@sensor_type_router.get(
    "/",
    response_model=list[SensorTypeResponse],
)
def get_sensor_types(
    db: Session = Depends(get_db),
):
    return db.query(SensorType).all()


@sensor_type_router.post(
    "/",
    response_model=SensorTypeResponse,
    status_code=201,
)
def create_sensor_type(
    sensor_type_data: SensorTypeCreate,
    db: Session = Depends(get_db),
):
    sensor_type = SensorType(
        **sensor_type_data.model_dump(),
    )

    db.add(sensor_type)
    db.commit()
    db.refresh(sensor_type)

    return sensor_type
