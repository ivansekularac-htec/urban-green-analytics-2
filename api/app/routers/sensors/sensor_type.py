from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.sensors import sensor_type as sensor_type_crud
from app.database import get_db
from app.schemas.sensors.sensor_type import SensorTypeCreate, SensorTypeResponse

router = APIRouter(prefix="/sensor_type", tags=["Sensor Type"])

DBSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/",
    response_model=SensorTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sensor_type(
    payload: SensorTypeCreate,
    db: DBSession,
) -> SensorTypeResponse:
    """
    Create a new sensor type.

    Args:
        payload: Sensor type data to create.
        db: Active database session.

    Returns:
        The newly created sensor type.
    """
    return sensor_type_crud.create(db, payload)


@router.get(
    "/{sensor_type_id}",
    response_model=SensorTypeResponse,
)
def get_sensor_type(
    sensor_type_id: int,
    db: DBSession,
) -> SensorTypeResponse:
    """
    Retrieve a sensor type by its ID.

    Args:
        sensor_type_id: Unique identifier of the sensor type.
        db: Active database session.

    Returns:
        The requested sensor type.

    Raises:
        HTTPException: If the sensor type does not exist.
    """
    sensor_type = sensor_type_crud.get(db, sensor_type_id)

    if sensor_type is None:
        raise HTTPException(
            status_code=404,
            detail="Sensor Type not found",
        )

    return sensor_type


@router.get(
    "/",
    response_model=list[SensorTypeResponse],
)
def get_sensor_types(
    db: DBSession,
) -> list[SensorTypeResponse]:
    """
    Retrieve all sensor types.

    Args:
        db: Active database session.

    Returns:
        A list of all sensor types.
    """
    return sensor_type_crud.get_all(db)
