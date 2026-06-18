"""
User API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.users.user import UserRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.users.user import UserCreate, UserResponse, UserUpdate
from app.security.dependencies import require_admin
from app.services.users.user import UserService

router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(require_admin())])


def get_user_service(db: DatabaseSession) -> UserService:
    """Create and return a User service instance."""
    return UserService(UserRepository(db))


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


@router.get("", response_model=list[UserResponse])
def list_users(service: UserServiceDep, pagination: PaginationDep):
    """List user records."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, service: UserServiceDep):
    """Get a user record by ID."""
    return service.get(user_id)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, service: UserServiceDep):
    """Create a user record."""
    return service.create(payload)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UserUpdate, service: UserServiceDep):
    """Update a user record by ID."""
    return service.update(user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, service: UserServiceDep):
    """Delete a user record by ID."""
    service.delete(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
