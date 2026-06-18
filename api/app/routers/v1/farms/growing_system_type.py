"""
Growing system type API routes.

Reference data — readable by any authenticated user; only Admin can write.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.farms.growing_system_type import GrowingSystemTypeRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.farms.growing_system_type import (
    GrowingSystemTypeCreate,
    GrowingSystemTypeResponse,
    GrowingSystemTypeUpdate,
)
from app.security.dependencies import get_current_user, require_roles
from app.security.roles import RoleName
from app.services.farms.growing_system_type import GrowingSystemTypeService

router = APIRouter(
    prefix="/growing-system-types",
    tags=["Growing System Types"],
    dependencies=[Depends(get_current_user)],
)


def get_growing_system_type_service(db: DatabaseSession) -> GrowingSystemTypeService:
    """Create and return a GrowingSystemType service instance."""
    return GrowingSystemTypeService(GrowingSystemTypeRepository(db))


GrowingSystemTypeServiceDep = Annotated[
    GrowingSystemTypeService,
    Depends(get_growing_system_type_service),
]


@router.get("", response_model=list[GrowingSystemTypeResponse])
def list_growing_system_types(service: GrowingSystemTypeServiceDep, pagination: PaginationDep):
    """List growing system type records."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{growing_system_type_id}", response_model=GrowingSystemTypeResponse)
def get_growing_system_type(
    growing_system_type_id: int,
    service: GrowingSystemTypeServiceDep,
):
    """Get a growing system type record by ID."""
    return service.get(growing_system_type_id)


@router.post(
    "",
    response_model=GrowingSystemTypeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
def create_growing_system_type(
    payload: GrowingSystemTypeCreate,
    service: GrowingSystemTypeServiceDep,
):
    """Create a growing system type record (Admin only)."""
    return service.create(payload)


@router.put(
    "/{growing_system_type_id}",
    response_model=GrowingSystemTypeResponse,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
def update_growing_system_type(
    growing_system_type_id: int,
    payload: GrowingSystemTypeUpdate,
    service: GrowingSystemTypeServiceDep,
):
    """Update a growing system type record by ID (Admin only)."""
    return service.update(growing_system_type_id, payload)


@router.delete(
    "/{growing_system_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
def delete_growing_system_type(
    growing_system_type_id: int,
    service: GrowingSystemTypeServiceDep,
):
    """Delete a growing system type record by ID (Admin only)."""
    service.delete(growing_system_type_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
