"""
roles.py
API routes for role management.

This module defines CRUD endpoints for Role resources.
"""

from fastapi import APIRouter, status

from app.database import SessionDep
from app.models.users.role import Role
from app.schemas.users.role import RoleCreate, RoleResponse, RoleUpdate
from app.services.common import get_or_404
from app.services.users import role_service

router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)


@router.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_role(
    role_data: RoleCreate,
    db: SessionDep,
) -> RoleResponse:
    """Create a new role."""
    return role_service.create_role(db, role_data)


@router.get(
    "",
    response_model=list[RoleResponse],
)
def get_roles(
    db: SessionDep,
) -> list[RoleResponse]:
    """Return all roles."""
    return role_service.get_roles(db)


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
)
def get_role(
    role_id: int,
    db: SessionDep,
) -> RoleResponse:
    """Return a role by ID."""

    return get_or_404(db, Role, role_id, "Role")


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
)
def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: SessionDep,
) -> RoleResponse:
    """Update a role by ID."""

    role = get_or_404(db, Role, role_id, "Role")

    return role_service.update_role(db, role, role_data)


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_role(
    role_id: int,
    db: SessionDep,
) -> None:
    """Delete a role by ID."""

    role = get_or_404(db, Role, role_id, "Role")

    role_service.delete_role(db, role)
