# from typing import Annotated

# from fastapi import APIRouter, Depends, Response, status

# from app.database import DatabaseSession
# from app.models.users.user import User
# from app.repositories.sensors.sensor import SensorRepository
# from app.routers.v1.auth.dependencies import (
#     CurrentUserDep,
#     assert_can_read_sensors,
#     assert_sensor_read_access,
#     require_admin,
# )
# from app.routers.v1.common.pagination import PaginationDep
# from app.schemas.sensors.sensor import SensorCreate, SensorResponse, SensorUpdate
# from app.services.sensors.sensor import SensorService

# router = APIRouter(prefix="/sensors", tags=["Sensors"])


# def get_sensor_service(db: DatabaseSession) -> SensorService:
#     """Create and return a Sensor service instance."""
#     return SensorService(SensorRepository(db))


# SensorServiceDep = Annotated[SensorService, Depends(get_sensor_service)]


# @router.get("", response_model=list[SensorResponse])
# def list_sensors(
#     service: SensorServiceDep,
#     current_user: CurrentUserDep,
#     pagination: PaginationDep,
#     farm_id: int | None = None,
# ):
#     """List sensor records.

#     - Admin/Operations: Can list all sensors, or filter by farm_id
#     - Farm Manager: Must provide farm_id and can only see their farm's sensors
#     """
#     assert_can_read_sensors(current_user)

#     if farm_id is not None:
#         assert_sensor_read_access(current_user, farm_id)
#         return service.list_by_farm(farm_id=farm_id, skip=pagination.skip, limit=pagination.limit)

#     # Admin/Operations can list all
#     return service.list(skip=pagination.skip, limit=pagination.limit)


# @router.get("/{sensor_id}", response_model=SensorResponse)
# def get_sensor(sensor_id: int, current_user: CurrentUserDep, service: SensorServiceDep):
#     """Get a sensor record by ID.

#     - Admin/Operations: Can read any sensor
#     - Farm Manager: Can only read sensors from their farm
#     """
#     assert_can_read_sensors(current_user)
#     sensor = service.get(sensor_id)
#     assert_sensor_read_access(current_user, sensor.farm_id)
#     return sensor


# @router.post("", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
# def create_sensor(
#     payload: SensorCreate,
#     service: SensorServiceDep,
#     user: Annotated[User, Depends(require_admin)],
# ):
#     """Create a sensor record (Admin only)."""
#     return service.create(payload)


# @router.put("/{sensor_id}", response_model=SensorResponse)
# def update_sensor(
#     sensor_id: int,
#     payload: SensorUpdate,
#     service: SensorServiceDep,
#     user: Annotated[User, Depends(require_admin)],
# ):
#     """Update a sensor record by ID (Admin only)."""
#     return service.update(sensor_id, payload)


# @router.delete("/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_sensor(
#     sensor_id: int,
#     service: SensorServiceDep,
#     user: Annotated[User, Depends(require_admin)],
# ):
#     """Delete a sensor record by ID (Admin only)."""
#     service.delete(sensor_id)
#     return Response(status_code=status.HTTP_204_NO_CONTENT)


"""
Sensor API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.sensors.sensor import SensorRepository
from app.routers.v1.auth.dependencies import (
    CurrentUserDep,
    assert_farm_access,
    is_admin,
    is_operations,
    user_farm_ids,
)
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.sensors.sensor import SensorCreate, SensorResponse, SensorUpdate
from app.security.rbac import require_roles
from app.services.sensors.sensor import SensorService

router = APIRouter(prefix="/sensors", tags=["Sensors"])


def get_sensor_service(db: DatabaseSession) -> SensorService:
    """Create and return a Sensor service instance."""
    return SensorService(SensorRepository(db))


SensorServiceDep = Annotated[
    SensorService,
    Depends(get_sensor_service),
]

ReadSensorsDep = Annotated[
    object,
    Depends(
        require_roles(
            "Admin",
            "Operations",
            "Farm Manager",
        )
    ),
]

ManageSensorsDep = Annotated[
    object,
    Depends(
        require_roles(
            "Admin",
        )
    ),
]


@router.get("", response_model=list[SensorResponse])
def list_sensors(
    service: SensorServiceDep,
    pagination: PaginationDep,
    current_user: CurrentUserDep,
    _: ReadSensorsDep,
):
    """
    List sensors.

    - Admin: sees all
    - Operations: sees all
    - Farm Manager: sees only their farms
    """

    if is_admin(current_user) or is_operations(current_user):
        return service.list(
            skip=pagination.skip,
            limit=pagination.limit,
        )

    return service.list_by_farm_ids(
        farm_ids=user_farm_ids(current_user),
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{sensor_id}", response_model=SensorResponse)
def get_sensor(
    sensor_id: int,
    service: SensorServiceDep,
    current_user: CurrentUserDep,
    _: ReadSensorsDep,
):
    """
    Get sensor by ID (with farm access check).
    """
    sensor = service.get(sensor_id)

    assert_farm_access(
        current_user,
        sensor.farm_id,
    )

    return sensor


@router.post(
    "",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sensor(
    payload: SensorCreate,
    service: SensorServiceDep,
    _: ManageSensorsDep,
):
    """
    Create sensor (Admin only).
    """
    return service.create(payload)


@router.put("/{sensor_id}", response_model=SensorResponse)
def update_sensor(
    sensor_id: int,
    payload: SensorUpdate,
    service: SensorServiceDep,
    _: ManageSensorsDep,
):
    """
    Update sensor (Admin only).
    """
    return service.update(sensor_id, payload)


@router.delete("/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sensor(
    sensor_id: int,
    service: SensorServiceDep,
    _: ManageSensorsDep,
):
    """
    Delete sensor (Admin only).
    """
    service.delete(sensor_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
