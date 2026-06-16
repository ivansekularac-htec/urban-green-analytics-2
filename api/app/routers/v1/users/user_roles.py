from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.database import DbSession
from app.models.users.user_roles import UserRole
from app.schemas.users.user_roles import (
    UserRoleCreate,
    UserRoleResponse,
    UserRoleUpdate,
)

user_roles_router = APIRouter(prefix="/user-roles", tags=["user-roles"])


@user_roles_router.post(
    "/",
    response_model=UserRoleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_role(
    payload: UserRoleCreate,
    db: DbSession,
) -> UserRole:
    user_role = UserRole(**payload.model_dump())

    db.add(user_role)
    db.commit()
    db.refresh(user_role)

    return user_role


@user_roles_router.get(
    "/",
    response_model=list[UserRoleResponse],
)
def get_user_roles(
    db: DbSession,
) -> list[UserRole]:
    return db.scalars(select(UserRole)).all()


@user_roles_router.get(
    "/{user_role_id}",
    response_model=UserRoleResponse,
)
def get_user_role(
    user_role_id: int,
    db: DbSession,
) -> UserRole:
    user_role = db.scalar(select(UserRole).where(UserRole.id == user_role_id))

    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User role not found",
        )

    return user_role


@user_roles_router.put(
    "/{user_role_id}",
    response_model=UserRoleResponse,
)
def update_user_role(
    user_role_id: int,
    payload: UserRoleUpdate,
    db: DbSession,
) -> UserRole:
    user_role = db.scalar(select(UserRole).where(UserRole.id == user_role_id))

    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User role not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user_role, field, value)

    db.commit()

    return user_role


@user_roles_router.delete(
    "/{user_role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user_role(
    user_role_id: int,
    db: DbSession,
) -> None:
    user_role = db.scalar(select(UserRole).where(UserRole.id == user_role_id))

    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User role not found",
        )

    db.delete(user_role)
    db.commit()
