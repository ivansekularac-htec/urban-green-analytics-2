"""
Sensor API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.dependencies.auth import (
    FARM_MANAGER_ROLE,
    AdminUserDep,
    SensorReadUserDep,
    require_farm_access,
    user_has_role,
)
from app.repositories.sensors.sensor import SensorRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.sensors.sensor import SensorCreate, SensorResponse, SensorUpdate
from app.services.sensors.sensor import SensorService

router = APIRouter(prefix="/sensors", tags=["Sensors"])


def get_sensor_service(db: DatabaseSession) -> SensorService:
    """Create and return a Sensor service instance."""
    return SensorService(SensorRepository(db))


SensorServiceDep = Annotated[SensorService, Depends(get_sensor_service)]


@router.get("", response_model=list[SensorResponse])
def list_sensors(
    service: SensorServiceDep, pagination: PaginationDep, current_user: SensorReadUserDep
):
    """List sensor records."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get(
    "/{sensor_id}",
    response_model=SensorResponse,
)
def get_sensor(sensor_id: int, service: SensorServiceDep, current_user: SensorReadUserDep):
    """Get a sensor record by ID."""
    sensor = service.get(sensor_id)

    if user_has_role(current_user, FARM_MANAGER_ROLE):
        require_farm_access(
            current_user,
            sensor.farm_id,
        )

    return sensor


@router.post("", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
def create_sensor(payload: SensorCreate, service: SensorServiceDep, current_user: AdminUserDep):
    """Create a sensor record."""
    return service.create(payload)


@router.put("/{sensor_id}", response_model=SensorResponse)
def update_sensor(
    sensor_id: int, payload: SensorUpdate, service: SensorServiceDep, current_user: AdminUserDep
):
    """Update a sensor record by ID."""
    return service.update(sensor_id, payload)


@router.delete("/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sensor(sensor_id: int, service: SensorServiceDep, current_user: AdminUserDep):
    """Delete a sensor record by ID."""
    service.delete(sensor_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
