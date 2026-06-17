from fastapi import APIRouter, HTTPException, status

from app.crud.sensors import sensor as sensor_crud
from app.routers.helpers import DBSession, PaginationDep
from app.schemas.sensors.sensor import SensorCreate, SensorResponse

router = APIRouter(prefix="/sensor", tags=["Sensor"])


@router.post(
    "/",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sensor(
    payload: SensorCreate,
    db: DBSession,
) -> SensorResponse:
    """
    Create a new sensor.

    Args:
        payload: Sensor data to create.
        db: Active database session.

    Returns:
        The newly created sensor.
    """
    return sensor_crud.create(db, payload)


@router.get(
    "/{sensor_id}",
    response_model=SensorResponse,
)
def get_sensor(
    sensor_id: int,
    db: DBSession,
) -> SensorResponse:
    """
    Retrieve a sensor by its ID.

    Args:
        sensor_id: Unique identifier of the sensor.
        db: Active database session.

    Returns:
        The requested sensor.

    Raises:
        HTTPException: If the sensor does not exist.
    """
    sensor = sensor_crud.get(db, sensor_id)

    if sensor is None:
        raise HTTPException(
            status_code=404,
            detail="Sensor not found",
        )

    return sensor


@router.get(
    "/",
    response_model=list[SensorResponse],
)
def get_sensors(
    db: DBSession,
    pagination: PaginationDep,
) -> list[SensorResponse]:
    """
    Retrieve all sensors.

    Args:
        db: Active database session.

    Returns:
        A list of all sensors.
    """
    return sensor_crud.get_all(
        db=db,
        skip=pagination.skip,
        limit=pagination.limit,
    )
