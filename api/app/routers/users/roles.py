"""
Role API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.users.role_repository import RoleRepository
from app.schemas.users.role import RoleCreate, RoleResponse, RoleUpdate
from app.services.users.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["Roles"])


def get_role_service(db: DatabaseSession) -> RoleService:
    """Create and return a Role service instance."""
    return RoleService(RoleRepository(db))


RoleServiceDep = Annotated[RoleService, Depends(get_role_service)]


@router.get("", response_model=list[RoleResponse])
def list_roles(service: RoleServiceDep, skip: int = 0, limit: int = 100):
    """List role records."""
    return service.list(skip=skip, limit=limit)


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(role_id: int, service: RoleServiceDep):
    """Get a role record by ID."""
    return service.get(role_id)


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleCreate, service: RoleServiceDep):
    """Create a role record."""
    return service.create(payload)


@router.put("/{role_id}", response_model=RoleResponse)
def update_role(role_id: int, payload: RoleUpdate, service: RoleServiceDep):
    """Update a role record by ID."""
    return service.update(role_id, payload)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, service: RoleServiceDep):
    """Delete a role record by ID."""
    service.delete(role_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
