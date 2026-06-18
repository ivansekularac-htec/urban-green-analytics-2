"""
Sensor type API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.sensors.sensor_type import SensorTypeRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.sensors.sensor_type import (
    SensorTypeCreate,
    SensorTypeResponse,
    SensorTypeUpdate,
)
from app.security.dependencies import get_current_active_user, require_admin
from app.services.sensors.sensor_type import SensorTypeService

router = APIRouter(
    prefix="/sensor-types",
    tags=["Sensor Types"],
    dependencies=[Depends(get_current_active_user)],
)


def get_sensor_type_service(db: DatabaseSession) -> SensorTypeService:
    """Create and return a SensorType service instance."""
    return SensorTypeService(SensorTypeRepository(db))


SensorTypeServiceDep = Annotated[SensorTypeService, Depends(get_sensor_type_service)]


@router.get("", response_model=list[SensorTypeResponse])
def list_sensor_types(service: SensorTypeServiceDep, pagination: PaginationDep):
    """List sensor type records."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{sensor_type_id}", response_model=SensorTypeResponse)
def get_sensor_type(sensor_type_id: int, service: SensorTypeServiceDep):
    """Get a sensor type record by ID."""
    return service.get(sensor_type_id)


@router.post(
    "",
    response_model=SensorTypeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_sensor_type(payload: SensorTypeCreate, service: SensorTypeServiceDep):
    """Create a sensor type record (Admin only)."""
    return service.create(payload)


@router.put(
    "/{sensor_type_id}",
    response_model=SensorTypeResponse,
    dependencies=[Depends(require_admin)],
)
def update_sensor_type(
    sensor_type_id: int,
    payload: SensorTypeUpdate,
    service: SensorTypeServiceDep,
):
    """Update a sensor type record by ID (Admin only)."""
    return service.update(sensor_type_id, payload)


@router.delete(
    "/{sensor_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_sensor_type(sensor_type_id: int, service: SensorTypeServiceDep):
    """Delete a sensor type record by ID (Admin only)."""
    service.delete(sensor_type_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
