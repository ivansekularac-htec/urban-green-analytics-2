"""
User API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.users.user import UserRepository
from app.routers.v1.auth.dependencies import (
    CurrentUserDep,
    assert_user_access,
    can_access_all_farms,
    get_accessible_farm_ids,
)
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.users.user import UserCreate, UserResponse, UserUpdate
from app.security.rbac import require_roles
from app.services.users.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(db: DatabaseSession) -> UserService:
    """Create and return a User service instance."""
    return UserService(UserRepository(db))


UserServiceDep = Annotated[UserService, Depends(get_user_service)]

ReadDep = Annotated[
    object,
    Depends(
        require_roles(
            "Admin",
            "Farm Manager",
        )
    ),
]

ManageDep = Annotated[
    object,
    Depends(
        require_roles(
            "Admin",
        )
    ),
]


# @router.get("", response_model=list[UserResponse])
# def list_users(service: UserServiceDep, current_user: CurrentUserDep, pagination: PaginationDep):
#     """List user records."""
#     return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("", response_model=list[UserResponse])
def list_users(
    service: UserServiceDep,
    current_user: CurrentUserDep,
    pagination: PaginationDep,
    _: ReadDep,
):
    """
    List users.

    Admin can see all users.
    Farm Managers can see only users belonging to their farms.
    """

    if can_access_all_farms(current_user):
        return service.list(
            skip=pagination.skip,
            limit=pagination.limit,
        )

    return service.list_by_farm_ids(
        farm_ids=get_accessible_farm_ids(current_user),
        skip=pagination.skip,
        limit=pagination.limit,
    )


# @router.get("/{user_id}", response_model=UserResponse)
# def get_user(user_id: int, current_user: CurrentUserDep, service: UserServiceDep):
#     """Get a user record by ID."""
#     return service.get(user_id)


@router.get("/{user_id}")
def get_user(
    user_id: int,
    service: UserServiceDep,
    current_user: CurrentUserDep,
    _: ReadDep,
):
    """
    Get a user record by ID.
    """
    user = service.get(user_id)

    assert_user_access(
        current_user,
        user,
    )

    return user


# @router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED,)
# def create_user(payload: UserCreate, service: UserServiceDep, current_user: CurrentUserDep):
#     """Create a user record."""
#     return service.create(payload)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    service: UserServiceDep,
    _: ManageDep,
):
    """
    Create a user record.
    """

    return service.create(payload)


# @router.put("/{user_id}", response_model=UserResponse)
# def update_user(
#     user_id: int, payload: UserUpdate, service: UserServiceDep, current_user: CurrentUserDep
# ):
#     """Update a user record by ID."""
#     return service.update(user_id, payload)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    service: UserServiceDep,
    _: ManageDep,
):
    """
    Update a user record by ID.
    """

    return service.update(user_id, payload)


# @router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_user(user_id: int, service: UserServiceDep, current_user: CurrentUserDep):
#     """Delete a user record by ID."""
#     service.delete(user_id)
#     return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    service: UserServiceDep,
    _: ManageDep,
):
    """
    Delete a user record by ID.
    """

    service.delete(user_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
