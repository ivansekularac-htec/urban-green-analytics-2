from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.users import role as user_role_crud
from app.database import get_db
from app.schemas.users.user_roles import UserRoleCreate, UserRoleResponse, UserRoleUpdate

router = APIRouter(prefix="/user_role", tags=["User Role"])

DBSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/",
    response_model=UserRoleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_role(
    payload: UserRoleCreate,
    db: DBSession,
) -> UserRoleResponse:
    """
    Create a new user role assignment.

    Args:
        payload: User role assignment data to create.
        db: Active database session.

    Returns:
        The newly created user role assignment.
    """
    return user_role_crud.create(db, payload)


@router.get(
    "/{user_role_id}",
    response_model=UserRoleResponse,
)
def get_user_role(
    user_role_id: int,
    db: DBSession,
) -> UserRoleResponse:
    """
    Retrieve a user role assignment by its ID.

    Args:
        user_role_id: Unique identifier of the user role assignment.
        db: Active database session.

    Returns:
        The requested user role assignment.

    Raises:
        HTTPException: If the user role assignment does not exist.
    """
    user_role = user_role_crud.get(db, user_role_id)

    if user_role is None:
        raise HTTPException(
            status_code=404,
            detail="User role not found",
        )

    return user_role


@router.get(
    "/",
    response_model=list[UserRoleResponse],
)
def get_user_roles(
    db: DBSession,
) -> list[UserRoleResponse]:
    """
    Retrieve all user role assignments.

    Args:
        db: Active database session.

    Returns:
        A list of all user role assignments.
    """
    return user_role_crud.get_all(db)


@router.put(
    "/{user_role_id}",
    response_model=UserRoleResponse,
)
def update_user_role(
    user_role_id: int,
    payload: UserRoleUpdate,
    db: DBSession,
) -> UserRoleResponse:
    """
    Update an existing user role assignment.

    Args:
        user_role_id: Unique identifier of the user role assignment.
        payload: Updated user role assignment data.
        db: Active database session.

    Returns:
        The updated user role assignment.

    Raises:
        HTTPException: If the user role assignment does not exist.
    """
    user_role = user_role_crud.get(
        db=db,
        user_role_id=user_role_id,
    )

    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User role not found",
        )

    return user_role_crud.update(
        db=db,
        user_role=user_role,
        payload=payload,
    )


@router.delete(
    "/{user_role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user_role(
    user_role_id: int,
    db: DBSession,
) -> None:
    """
    Delete a user role assignment.

    Args:
        user_role_id: Unique identifier of the user role assignment.
        db: Active database session.

    Raises:
        HTTPException: If the user role assignment does not exist.
    """
    user_role = user_role_crud.get(
        db=db,
        user_role_id=user_role_id,
    )

    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User role not found",
        )

    user_role_crud.delete(
        db=db,
        user_role=user_role,
    )
