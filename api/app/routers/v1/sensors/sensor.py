"""
Sensor API routes.

Read access is open to all authenticated roles, scoped to the farms the
user is assigned to (Admin sees everything). Writes are Admin only.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.sensors.sensor import SensorRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.sensors.sensor import SensorCreate, SensorResponse, SensorUpdate
from app.security.dependencies import (
    AccessibleFarms,
    assert_farm_in_scope,
    get_current_user,
    require_roles,
)
from app.security.roles import RoleName
from app.services.sensors.sensor import SensorService

router = APIRouter(
    prefix="/sensors",
    tags=["Sensors"],
    dependencies=[Depends(get_current_user)],
)


def get_sensor_service(db: DatabaseSession) -> SensorService:
    """Create and return a Sensor service instance."""
    return SensorService(SensorRepository(db))


SensorServiceDep = Annotated[SensorService, Depends(get_sensor_service)]


@router.get("", response_model=list[SensorResponse])
def list_sensors(service: SensorServiceDep, pagination: PaginationDep, farms: AccessibleFarms):
    """List sensor records visible to the current user."""
    return service.list(skip=pagination.skip, limit=pagination.limit, farm_ids=farms)


@router.get("/{sensor_id}", response_model=SensorResponse)
def get_sensor(sensor_id: int, service: SensorServiceDep, farms: AccessibleFarms):
    """Get a sensor record by ID, scoped to the user's farms."""
    sensor = service.get(sensor_id)
    assert_farm_in_scope(sensor.farm_id, farms)
    return sensor


@router.post(
    "",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
def create_sensor(payload: SensorCreate, service: SensorServiceDep):
    """Create a sensor record (Admin only)."""
    return service.create(payload)


@router.put(
    "/{sensor_id}",
    response_model=SensorResponse,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
def update_sensor(sensor_id: int, payload: SensorUpdate, service: SensorServiceDep):
    """Update a sensor record by ID (Admin only)."""
    return service.update(sensor_id, payload)


@router.delete(
    "/{sensor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
def delete_sensor(sensor_id: int, service: SensorServiceDep):
    """Delete a sensor record by ID (Admin only)."""
    service.delete(sensor_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
