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
from app.security.rbac import require_roles
from app.services.sensors.sensor_type import SensorTypeService

router = APIRouter(prefix="/sensor-types", tags=["Sensor Types"])


def get_sensor_type_service(db: DatabaseSession) -> SensorTypeService:
    """Create and return a SensorType service instance."""
    return SensorTypeService(SensorTypeRepository(db))


SensorTypeServiceDep = Annotated[SensorTypeService, Depends(get_sensor_type_service)]


ReadDep = Annotated[
    object,
    Depends(
        require_roles(
            "Admin",
            "Operations",
            "Farm Manager",
        )
    ),
]

AdminDep = Annotated[
    object,
    Depends(
        require_roles(
            "Admin",
        )
    ),
]


@router.get("", response_model=list[SensorTypeResponse])
def list_sensor_types(service: SensorTypeServiceDep, _: ReadDep, pagination: PaginationDep):
    """List sensor type records."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{sensor_type_id}", response_model=SensorTypeResponse)
def get_sensor_type(
    sensor_type_id: int,
    _: ReadDep,
    service: SensorTypeServiceDep,
):
    """Get a sensor type record by ID."""
    return service.get(sensor_type_id)


@router.post("", response_model=SensorTypeResponse, status_code=status.HTTP_201_CREATED)
def create_sensor_type(
    payload: SensorTypeCreate,
    service: SensorTypeServiceDep,
    _: AdminDep,
):
    """Create a sensor type record."""
    return service.create(payload)


@router.put("/{sensor_type_id}", response_model=SensorTypeResponse)
def update_sensor_type(
    sensor_type_id: int,
    payload: SensorTypeUpdate,
    service: SensorTypeServiceDep,
    _: AdminDep,
):
    """Update a sensor type record by ID."""
    return service.update(sensor_type_id, payload)


@router.delete("/{sensor_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sensor_type(
    sensor_type_id: int,
    service: SensorTypeServiceDep,
    _: AdminDep,
):
    """Delete a sensor type record by ID."""
    service.delete(sensor_type_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
