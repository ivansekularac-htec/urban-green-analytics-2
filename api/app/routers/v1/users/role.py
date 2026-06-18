"""
Role API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.users.role import RoleRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.users.role import RoleCreate, RoleResponse, RoleUpdate
from app.security.rbac import require_roles
from app.services.users.role import RoleService

router = APIRouter(prefix="/roles", tags=["Roles"])


def get_role_service(db: DatabaseSession) -> RoleService:
    """Create and return a Role service instance."""
    return RoleService(RoleRepository(db))


RoleServiceDep = Annotated[RoleService, Depends(get_role_service)]

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


@router.get("", response_model=list[RoleResponse])
def list_roles(
    service: RoleServiceDep,
    _: ReadDep,
    pagination: PaginationDep,
):
    """List role records."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: int,
    _: ReadDep,
    service: RoleServiceDep,
):
    """Get a role record by ID."""
    return service.get(role_id)


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreate,
    service: RoleServiceDep,
    _: AdminDep,
):
    """Create a role record."""
    return service.create(payload)


@router.put("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    payload: RoleUpdate,
    service: RoleServiceDep,
    _: AdminDep,
):
    """Update a role record by ID."""
    return service.update(role_id, payload)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    service: RoleServiceDep,
    _: AdminDep,
):
    """Delete a role record by ID."""
    service.delete(role_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
