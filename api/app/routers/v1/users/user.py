from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.users.user import UserCreate, UserResponse, UserUpdate
from app.services.users import user as user_service

router = APIRouter(prefix="/users", tags=["users"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[UserResponse])
def get_users(db: DbSession):
    """List all users."""
    return user_service.get_users(db)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: DbSession):
    """Retrieve a single user by ID."""
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: DbSession):
    """Create a new user."""
    return user_service.create_user(db, payload)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UserUpdate, db: DbSession):
    """Update an existing user."""
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_service.update_user(db, user, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: DbSession):
    """Delete a user."""
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user_service.delete_user(db, user)
