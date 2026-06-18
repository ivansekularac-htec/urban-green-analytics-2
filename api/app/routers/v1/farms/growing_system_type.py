"""
Growing system type API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.dependencies.auth import AdminUserDep, AuthenticatedUserDep
from app.repositories.farms.growing_system_type import GrowingSystemTypeRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.farms.growing_system_type import (
    GrowingSystemTypeCreate,
    GrowingSystemTypeResponse,
    GrowingSystemTypeUpdate,
)
from app.services.farms.growing_system_type import GrowingSystemTypeService

router = APIRouter(prefix="/growing-system-types", tags=["Growing System Types"])


def get_growing_system_type_service(db: DatabaseSession) -> GrowingSystemTypeService:
    """Create and return a GrowingSystemType service instance."""
    return GrowingSystemTypeService(GrowingSystemTypeRepository(db))


GrowingSystemTypeServiceDep = Annotated[
    GrowingSystemTypeService,
    Depends(get_growing_system_type_service),
]


@router.get("", response_model=list[GrowingSystemTypeResponse])
def list_growing_system_types(
    service: GrowingSystemTypeServiceDep,
    pagination: PaginationDep,
    current_user: AuthenticatedUserDep,
):
    """List growing system type records."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{growing_system_type_id}", response_model=GrowingSystemTypeResponse)
def get_growing_system_type(
    growing_system_type_id: int,
    service: GrowingSystemTypeServiceDep,
    current_user: AuthenticatedUserDep,
):
    """Get a growing system type record by ID."""
    return service.get(growing_system_type_id)


@router.post(
    "",
    response_model=GrowingSystemTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_growing_system_type(
    payload: GrowingSystemTypeCreate,
    service: GrowingSystemTypeServiceDep,
    current_user: AdminUserDep,
):
    """Create a growing system type record."""
    return service.create(payload)


@router.put("/{growing_system_type_id}", response_model=GrowingSystemTypeResponse)
def update_growing_system_type(
    growing_system_type_id: int,
    payload: GrowingSystemTypeUpdate,
    service: GrowingSystemTypeServiceDep,
    current_user: AdminUserDep,
):
    """Update a growing system type record by ID."""
    return service.update(growing_system_type_id, payload)


@router.delete("/{growing_system_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_growing_system_type(
    growing_system_type_id: int,
    service: GrowingSystemTypeServiceDep,
    current_user: AdminUserDep,
):
    """Delete a growing system type record by ID."""
    service.delete(growing_system_type_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
