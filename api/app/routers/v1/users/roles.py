from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.database import DbSession
from app.models.users.role import Role
from app.schemas.users.role import (
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)

roles_router = APIRouter(prefix="/roles", tags=["roles"])


@roles_router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_role(
    payload: RoleCreate,
    db: DbSession,
) -> Role:
    role = Role(**payload.model_dump())

    db.add(role)
    db.commit()
    db.refresh(role)

    return role


@roles_router.get(
    "/",
    response_model=list[RoleResponse],
)
def get_roles(
    db: DbSession,
) -> list[Role]:
    return db.scalars(select(Role)).all()


@roles_router.get(
    "/{role_id}",
    response_model=RoleResponse,
)
def get_role(
    role_id: int,
    db: DbSession,
) -> Role:
    role = db.scalar(select(Role).where(Role.id == role_id))

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    return role


@roles_router.put(
    "/{role_id}",
    response_model=RoleResponse,
)
def update_role(
    role_id: int,
    payload: RoleUpdate,
    db: DbSession,
) -> Role:
    role = db.scalar(select(Role).where(Role.id == role_id))

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(role, field, value)

    db.commit()

    return role


@roles_router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_role(
    role_id: int,
    db: DbSession,
) -> None:
    role = db.scalar(select(Role).where(Role.id == role_id))

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    db.delete(role)
    db.commit()
