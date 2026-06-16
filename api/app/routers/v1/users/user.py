"""
users.py
API routes for user management.

This module defines CRUD endpoints for User resources.
"""

from fastapi import APIRouter, status

from app.database import SessionDep
from app.models.users.user import User
from app.schemas.users.user import UserCreate, UserPasswordUpdate, UserResponse, UserUpdate
from app.services.common import get_or_404
from app.services.users import user_service

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user_data: UserCreate,
    db: SessionDep,
) -> UserResponse:
    """Create a new user."""
    return user_service.create_user(db, user_data)


@router.get(
    "",
    response_model=list[UserResponse],
)
def get_users(
    db: SessionDep,
) -> list[UserResponse]:
    """Return all users."""
    return user_service.get_users(db)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    db: SessionDep,
) -> UserResponse:
    """Return a user by ID."""
    return get_or_404(db, User, user_id, "User")


@router.put(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: SessionDep,
) -> UserResponse:
    """Update a user by ID."""
    user = get_or_404(db, User, user_id, "User")

    return user_service.update_user(db, user, user_data)


@router.put(
    "/{user_id}/password",
    response_model=UserResponse,
)
def update_user_password(
    user_id: int,
    password_data: UserPasswordUpdate,
    db: SessionDep,
) -> UserResponse:
    """Update a user's password by ID."""
    user = get_or_404(db, User, user_id, "User")

    return user_service.update_user_password(db, user, password_data)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(
    user_id: int,
    db: SessionDep,
) -> None:
    """Delete a user by ID."""
    user = get_or_404(db, User, user_id, "User")

    user_service.delete_user(db, user)
