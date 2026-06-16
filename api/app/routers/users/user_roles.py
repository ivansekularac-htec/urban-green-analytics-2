"""
UserRole API routes.
"""

from fastapi import APIRouter, Response, status

from app.database import DbSession
from app.schemas.users.user_roles import (
    UserRoleCreate,
    UserRoleResponse,
    UserRoleUpdate,
)
from app.services.users.user_roles import UserRoleService

user_role_router = APIRouter(
    prefix="/user-roles",
    tags=["User Roles"],
)

user_role_service = UserRoleService()


@user_role_router.get("/", response_model=list[UserRoleResponse])
def get_user_roles(
    db: DbSession,
):
    return user_role_service.get_all(db)


@user_role_router.get("/{user_role_id}", response_model=UserRoleResponse)
def get_user_role(
    user_role_id: int,
    db: DbSession = DbSession,
):
    return user_role_service.get(
        db,
        user_role_id,
    )


@user_role_router.post("/", response_model=UserRoleResponse, status_code=status.HTTP_201_CREATED)
def create_user_role(
    data: UserRoleCreate,
    db: DbSession,
):
    return user_role_service.create(
        db,
        data,
    )


@user_role_router.put("/{user_role_id}", response_model=UserRoleResponse)
def update_user_role(
    user_role_id: int,
    data: UserRoleUpdate,
    db: DbSession,
):
    return user_role_service.update(
        db,
        user_role_id,
        data,
    )


@user_role_router.delete("/{user_role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_role(
    user_role_id: int,
    db: DbSession,
):
    user_role_service.delete(
        db,
        user_role_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
