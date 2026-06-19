"""
User role API routes.

Admin-only — role assignments are managed by system administrators.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.users.user_role import UserRoleRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.users.user_roles import UserRoleCreate, UserRoleResponse, UserRoleUpdate
from app.security.dependencies import require_roles
from app.security.roles import RoleName
from app.services.users.user_role import UserRoleService

router = APIRouter(
    prefix="/user-roles",
    tags=["User Roles"],
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)


def get_user_role_service(db: DatabaseSession) -> UserRoleService:
    """Create and return a UserRole service instance."""
    return UserRoleService(UserRoleRepository(db))


UserRoleServiceDep = Annotated[UserRoleService, Depends(get_user_role_service)]


@router.get("", response_model=list[UserRoleResponse])
def list_user_roles(service: UserRoleServiceDep, pagination: PaginationDep):
    """List user role records."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{user_role_id}", response_model=UserRoleResponse)
def get_user_role(user_role_id: int, service: UserRoleServiceDep):
    """Get a user role record by ID."""
    return service.get(user_role_id)


@router.post("", response_model=UserRoleResponse, status_code=status.HTTP_201_CREATED)
def create_user_role(payload: UserRoleCreate, service: UserRoleServiceDep):
    """Create a user role record."""
    return service.create(payload)


@router.put("/{user_role_id}", response_model=UserRoleResponse)
def update_user_role(
    user_role_id: int,
    payload: UserRoleUpdate,
    service: UserRoleServiceDep,
):
    """Update a user role record by ID."""
    return service.update(user_role_id, payload)


@router.delete("/{user_role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_role(user_role_id: int, service: UserRoleServiceDep):
    """Delete a user role record by ID."""
    service.delete(user_role_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
