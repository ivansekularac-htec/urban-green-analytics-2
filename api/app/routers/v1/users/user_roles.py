"""
user_roles.py
API routes for user role management.

This module defines CRUD endpoints for UserRole resources.
"""

from fastapi import APIRouter, status

from app.database import SessionDep
from app.models.farms.farm import Farm
from app.models.users.role import Role
from app.models.users.user import User
from app.models.users.user_roles import UserRole
from app.schemas.users.user_roles import UserRoleCreate, UserRoleResponse, UserRoleUpdate
from app.services.common import get_or_404
from app.services.users import user_roles_service

router = APIRouter(
    prefix="/user-roles",
    tags=["User Roles"],
)


@router.post("", response_model=UserRoleResponse, status_code=status.HTTP_201_CREATED)
def create_user_role(user_role_data: UserRoleCreate, db: SessionDep) -> UserRoleResponse:
    """Create a new user role assignment."""
    get_or_404(db, User, user_role_data.user_id, "User")
    get_or_404(db, Role, user_role_data.role_id, "Role")

    if user_role_data.farm_id is not None:
        get_or_404(db, Farm, user_role_data.farm_id, "Farm")

    return user_roles_service.create_user_role(db, user_role_data)


@router.get("", response_model=list[UserRoleResponse])
def get_user_roles(db: SessionDep) -> list[UserRoleResponse]:
    """Return all user role assignments."""
    return user_roles_service.get_user_roles(db)


@router.get("/{user_role_id}", response_model=UserRoleResponse)
def get_user_role(user_role_id: int, db: SessionDep) -> UserRoleResponse:
    """Return a user role assignment by ID."""
    return get_or_404(db, UserRole, user_role_id, "User role")


@router.put("/{user_role_id}", response_model=UserRoleResponse)
def update_user_role(
    user_role_id: int,
    user_role_data: UserRoleUpdate,
    db: SessionDep,
) -> UserRoleResponse:
    """Update a user role assignment by ID."""
    user_role = get_or_404(db, UserRole, user_role_id, "User role")

    if user_role_data.user_id is not None:
        get_or_404(db, User, user_role_data.user_id, "User")

    if user_role_data.role_id is not None:
        get_or_404(db, Role, user_role_data.role_id, "Role")

    if user_role_data.farm_id is not None:
        get_or_404(db, Farm, user_role_data.farm_id, "Farm")

    return user_roles_service.update_user_role(db, user_role, user_role_data)


@router.delete("/{user_role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_role(user_role_id: int, db: SessionDep) -> None:
    """Delete a user role assignment by ID."""
    user_role = get_or_404(db, UserRole, user_role_id, "User role")

    user_roles_service.delete_user_role(db, user_role)
