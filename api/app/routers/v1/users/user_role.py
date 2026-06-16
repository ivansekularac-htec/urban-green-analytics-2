from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.users.user_roles import UserRoleCreate, UserRoleResponse, UserRoleUpdate
from app.services.users import user_role as user_role_service

router = APIRouter(prefix="/user-roles", tags=["user-roles"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[UserRoleResponse])
def get_user_roles(db: DbSession):
    """List all user roles."""
    return user_role_service.get_user_roles(db)


@router.get("/{user_role_id}", response_model=UserRoleResponse)
def get_user_role(user_role_id: int, db: DbSession):
    """Retrieve a single user role by ID."""
    user_role = user_role_service.get_user_role(db, user_role_id)
    if not user_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User role not found")
    return user_role


@router.post("/", response_model=UserRoleResponse, status_code=status.HTTP_201_CREATED)
def create_user_role(payload: UserRoleCreate, db: DbSession):
    """Create a new user role."""
    return user_role_service.create_user_role(db, payload)


@router.put("/{user_role_id}", response_model=UserRoleResponse)
def update_user_role(user_role_id: int, payload: UserRoleUpdate, db: DbSession):
    """Update an existing user role."""
    user_role = user_role_service.get_user_role(db, user_role_id)
    if not user_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User role not found")
    return user_role_service.update_user_role(db, user_role, payload)


@router.delete("/{user_role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_role(user_role_id: int, db: DbSession):
    """Delete a user role."""
    user_role = user_role_service.get_user_role(db, user_role_id)
    if not user_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User role not found")
    user_role_service.delete_user_role(db, user_role)
