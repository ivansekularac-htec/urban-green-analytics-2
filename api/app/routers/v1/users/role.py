"""
Role API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.dependencies.auth import AdminUserDep, AuthenticatedUserDep
from app.repositories.users.role import RoleRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.users.role import RoleCreate, RoleResponse, RoleUpdate
from app.services.users.role import RoleService

router = APIRouter(prefix="/roles", tags=["Roles"])


def get_role_service(db: DatabaseSession) -> RoleService:
    """Create and return a Role service instance."""
    return RoleService(RoleRepository(db))


RoleServiceDep = Annotated[RoleService, Depends(get_role_service)]


@router.get("", response_model=list[RoleResponse])
def list_roles(
    service: RoleServiceDep, pagination: PaginationDep, current_user: AuthenticatedUserDep
):
    """List role records."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(role_id: int, service: RoleServiceDep, current_user: AuthenticatedUserDep):
    """Get a role record by ID."""
    return service.get(role_id)


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleCreate, service: RoleServiceDep, current_user: AdminUserDep):
    """Create a role record."""
    return service.create(payload)


@router.put("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int, payload: RoleUpdate, service: RoleServiceDep, current_user: AdminUserDep
):
    """Update a role record by ID."""
    return service.update(role_id, payload)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, service: RoleServiceDep, current_user: AdminUserDep):
    """Delete a role record by ID."""
    service.delete(role_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
