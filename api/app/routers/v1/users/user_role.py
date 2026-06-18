"""
User role API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.dependencies.auth import AdminUserDep
from app.repositories.users.user_role import UserRoleRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.users.user_roles import UserRoleCreate, UserRoleResponse, UserRoleUpdate
from app.services.users.user_role import UserRoleService

router = APIRouter(prefix="/user-roles", tags=["User Roles"])


def get_user_role_service(db: DatabaseSession) -> UserRoleService:
    """Create and return a UserRole service instance."""
    return UserRoleService(UserRoleRepository(db))


UserRoleServiceDep = Annotated[UserRoleService, Depends(get_user_role_service)]


@router.get("", response_model=list[UserRoleResponse])
def list_user_roles(
    service: UserRoleServiceDep, pagination: PaginationDep, current_user: AdminUserDep
):
    """List user role records."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{user_role_id}", response_model=UserRoleResponse)
def get_user_role(user_role_id: int, service: UserRoleServiceDep, current_user: AdminUserDep):
    """Get a user role record by ID."""
    return service.get(user_role_id)


@router.post("", response_model=UserRoleResponse, status_code=status.HTTP_201_CREATED)
def create_user_role(
    payload: UserRoleCreate, service: UserRoleServiceDep, current_user: AdminUserDep
):
    """Create a user role record."""
    return service.create(payload)


@router.put("/{user_role_id}", response_model=UserRoleResponse)
def update_user_role(
    user_role_id: int,
    payload: UserRoleUpdate,
    service: UserRoleServiceDep,
    current_user: AdminUserDep,
):
    """Update a user role record by ID."""
    return service.update(user_role_id, payload)


@router.delete("/{user_role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_role(user_role_id: int, service: UserRoleServiceDep, current_user: AdminUserDep):
    """Delete a user role record by ID."""
    service.delete(user_role_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
