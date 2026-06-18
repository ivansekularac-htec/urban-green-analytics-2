"""
Sensor API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.sensors.sensor import SensorRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.sensors.sensor import SensorCreate, SensorResponse, SensorUpdate
from app.security.dependencies import require_roles
from app.services.sensors.sensor import SensorService

router = APIRouter(prefix="/sensors", tags=["Sensors"])


def get_sensor_service(db: DatabaseSession) -> SensorService:
    """Create and return a Sensor service instance."""
    return SensorService(SensorRepository(db))


SensorServiceDep = Annotated[SensorService, Depends(get_sensor_service)]

admin_operations_farm_manager_dep = Depends(require_roles("admin", "operations", "farm manager"))
admin_only_dep = Depends(require_roles("admin"))


@router.get("", response_model=list[SensorResponse])
def list_sensors(
    service: SensorServiceDep,
    pagination: PaginationDep,
    user: dict = admin_operations_farm_manager_dep,
):
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{sensor_id}", response_model=SensorResponse)
def get_sensor(sensor_id: int, service: SensorServiceDep):
    """Get a sensor record by ID."""
    return service.get(sensor_id)


@router.post("", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
def create_sensor(
    payload: SensorCreate,
    service: SensorServiceDep,
    user: dict = admin_only_dep,
):
    return service.create(payload)


@router.put("/{sensor_id}", response_model=SensorResponse)
def update_sensor(sensor_id: int, payload: SensorUpdate, service: SensorServiceDep):
    """Update a sensor record by ID."""
    return service.update(sensor_id, payload)


@router.delete("/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sensor(sensor_id: int, service: SensorServiceDep):
    """Delete a sensor record by ID."""
    service.delete(sensor_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
