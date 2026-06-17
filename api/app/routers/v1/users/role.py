from typing import Annotated

from app.services.users import role as role_service
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.users.role import RoleCreate, RoleResponse, RoleUpdate

router = APIRouter(prefix="/roles", tags=["roles"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[RoleResponse])
def get_roles(db: DbSession):
    """List all roles."""
    return role_service.get_roles(db)


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(role_id: int, db: DbSession):
    """Retrieve a single role by ID."""
    role = role_service.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleCreate, db: DbSession):
    """Create a new role."""
    return role_service.create_role(db, payload)


@router.put("/{role_id}", response_model=RoleResponse)
def update_role(role_id: int, payload: RoleUpdate, db: DbSession):
    """Update an existing role."""
    role = role_service.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role_service.update_role(db, role, payload)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, db: DbSession):
    """Delete a role."""
    role = role_service.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    role_service.delete_role(db, role)
