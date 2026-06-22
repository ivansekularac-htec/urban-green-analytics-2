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
    can_access_all_farms,
    get_accessible_farm_ids,
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

ReadDep = Annotated[
    object,
    Depends(
        require_roles(
            "Admin",
            "Operations Team",
            "Farm Manager",
        )
    ),
]

ManageDep = Annotated[
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
    _: ReadDep,
):
    if can_access_all_farms(current_user):
        return service.list(
            skip=pagination.skip,
            limit=pagination.limit,
        )

    return service.list_by_farm_ids(
        farm_ids=get_accessible_farm_ids(current_user),
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{sensor_id}", response_model=SensorResponse)
def get_sensor(
    sensor_id: int,
    service: SensorServiceDep,
    current_user: CurrentUserDep,
    _: ReadDep,
):
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
    _: ManageDep,
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
    _: ManageDep,
):
    """
    Update sensor (Admin only).
    """
    return service.update(sensor_id, payload)


@router.delete("/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sensor(
    sensor_id: int,
    service: SensorServiceDep,
    _: ManageDep,
):
    """
    Delete sensor (Admin only).
    """
    service.delete(sensor_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
