"""
Role API routes.
"""

from fastapi import APIRouter, Response, status

from app.database import DbSession
from app.schemas.users.role import (
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)
from app.services.users.role import RoleService

role_router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)

role_service = RoleService()


@role_router.get("/", response_model=list[RoleResponse])
def get_roles(db: DbSession):
    """
    Retrieve all roles.
    """

    return role_service.get_all(db)


@role_router.get("/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: int,
    db: DbSession,
):
    """
    Retrieve a role by ID.
    """

    return role_service.get(db, role_id)


@role_router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    data: RoleCreate,
    db: DbSession,
):
    """
    Create a new role.
    """

    return role_service.create(db, data)


@role_router.put("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    data: RoleUpdate,
    db: DbSession,
):
    """
    Update an existing role.
    """

    return role_service.update(
        db,
        role_id,
        data,
    )


@role_router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    db: DbSession,
):
    """
    Delete a role.
    """

    role_service.delete(db, role_id)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
