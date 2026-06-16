"""
API routes for User.
"""

from fastapi import APIRouter, Response, status

from app.database import DbSession
from app.schemas.users.user import (
    UserCreate,
    UserPasswordUpdate,
    UserResponse,
    UserUpdate,
)
from app.services.users.user import UserService

user_router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

user_service = UserService()


@user_router.get("/", response_model=list[UserResponse])
def get_users(db: DbSession):
    """
    Retrieve all users.
    """

    return user_service.get_all(db)


@user_router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: DbSession,
):
    """
    Retrieve a user by ID.
    """

    return user_service.get(db, user_id)


@user_router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    db: DbSession,
):
    """
    Create a new user.
    """

    return user_service.create(db, data)


@user_router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: DbSession,
):
    """
    Update an existing user.
    """

    return user_service.update(db, user_id, data)


@user_router.put("/{user_id}/password", response_model=UserResponse)
def update_user_password(
    user_id: int,
    data: UserPasswordUpdate,
    db: DbSession,
):
    """
    Change user password.
    """

    return user_service.update_password(
        db=db,
        user_id=user_id,
        data=data,
    )


@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: DbSession,
):
    """
    Delete a user.
    """

    user_service.delete(db, user_id)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
