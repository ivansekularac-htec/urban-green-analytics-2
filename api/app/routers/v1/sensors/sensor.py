"""
Sensor API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.sensors.sensor import SensorRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.sensors.sensor import SensorCreate, SensorResponse, SensorUpdate
from app.security.dependencies import CurrentActiveUser, require_admin
from app.services.sensors.sensor import SensorService

router = APIRouter(prefix="/sensors", tags=["Sensors"])


def get_sensor_service(db: DatabaseSession, current_user: CurrentActiveUser) -> SensorService:
    """Create and return a Sensor service instance scoped to the current user."""
    return SensorService(SensorRepository(db), current_user)


SensorServiceDep = Annotated[SensorService, Depends(get_sensor_service)]


@router.get("", response_model=list[SensorResponse])
def list_sensors(service: SensorServiceDep, pagination: PaginationDep):
    """List sensor records visible to the current user."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{sensor_id}", response_model=SensorResponse)
def get_sensor(sensor_id: int, service: SensorServiceDep):
    """Get a sensor record by ID."""
    return service.get(sensor_id)


@router.post(
    "",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_sensor(payload: SensorCreate, service: SensorServiceDep):
    """Create a sensor record (Admin only)."""
    return service.create(payload)


@router.put("/{sensor_id}", response_model=SensorResponse, dependencies=[Depends(require_admin)])
def update_sensor(sensor_id: int, payload: SensorUpdate, service: SensorServiceDep):
    """Update a sensor record by ID (Admin only)."""
    return service.update(sensor_id, payload)


@router.delete(
    "/{sensor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_sensor(sensor_id: int, service: SensorServiceDep):
    """Delete a sensor record by ID (Admin only)."""
    service.delete(sensor_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
