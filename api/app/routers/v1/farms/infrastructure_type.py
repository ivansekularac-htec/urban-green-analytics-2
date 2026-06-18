"""
Infrastructure type API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.farms.infrastructure_type import InfrastructureTypeRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.farms.infrastructure_type import (
    InfrastructureTypeCreate,
    InfrastructureTypeResponse,
    InfrastructureTypeUpdate,
)
from app.security.dependencies import get_current_active_user, require_admin
from app.services.farms.infrastructure_type import InfrastructureTypeService

router = APIRouter(
    prefix="/infrastructure-types",
    tags=["Infrastructure Types"],
    dependencies=[Depends(get_current_active_user)],
)


def get_infrastructure_type_service(db: DatabaseSession) -> InfrastructureTypeService:
    """Create and return an InfrastructureType service instance."""
    return InfrastructureTypeService(InfrastructureTypeRepository(db))


InfrastructureTypeServiceDep = Annotated[
    InfrastructureTypeService,
    Depends(get_infrastructure_type_service),
]


@router.get("", response_model=list[InfrastructureTypeResponse])
def list_infrastructure_types(service: InfrastructureTypeServiceDep, pagination: PaginationDep):
    """List infrastructure type records."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{infrastructure_type_id}", response_model=InfrastructureTypeResponse)
def get_infrastructure_type(
    infrastructure_type_id: int,
    service: InfrastructureTypeServiceDep,
):
    """Get an infrastructure type record by ID."""
    return service.get(infrastructure_type_id)


@router.post(
    "",
    response_model=InfrastructureTypeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_infrastructure_type(
    payload: InfrastructureTypeCreate,
    service: InfrastructureTypeServiceDep,
):
    """Create an infrastructure type record."""
    return service.create(payload)


@router.put(
    "/{infrastructure_type_id}",
    response_model=InfrastructureTypeResponse,
    dependencies=[Depends(require_admin)],
)
def update_infrastructure_type(
    infrastructure_type_id: int,
    payload: InfrastructureTypeUpdate,
    service: InfrastructureTypeServiceDep,
):
    """Update an infrastructure type record by ID."""
    return service.update(infrastructure_type_id, payload)


@router.delete(
    "/{infrastructure_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_infrastructure_type(
    infrastructure_type_id: int,
    service: InfrastructureTypeServiceDep,
):
    """Delete an infrastructure type record by ID."""
    service.delete(infrastructure_type_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
