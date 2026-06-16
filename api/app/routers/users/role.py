from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.users import role as role_crud
from app.database import get_db
from app.schemas.users.role import RoleCreate, RoleResponse, RoleUpdate

router = APIRouter(prefix="/role", tags=["Role"])

DBSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_role(
    payload: RoleCreate,
    db: DBSession,
) -> RoleResponse:
    """
    Create a new role.

    Args:
        payload: Role data to create.
        db: Active database session.

    Returns:
        The newly created role.
    """
    return role_crud.create(db, payload)


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
)
def get_role(
    role_id: int,
    db: DBSession,
) -> RoleResponse:
    """
    Retrieve a role by its ID.

    Args:
        role_id: Unique identifier of the role.
        db: Active database session.

    Returns:
        The requested role.

    Raises:
        HTTPException: If the role does not exist.
    """
    role = role_crud.get(db, role_id)

    if role is None:
        raise HTTPException(
            status_code=404,
            detail="Role not found",
        )

    return role


@router.get(
    "/",
    response_model=list[RoleResponse],
)
def get_roles(
    db: DBSession,
) -> list[RoleResponse]:
    """
    Retrieve all roles.

    Args:
        db: Active database session.

    Returns:
        A list of all roles.
    """
    return role_crud.get_all(db)


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
)
def update_role(
    role_id: int,
    payload: RoleUpdate,
    db: DBSession,
) -> RoleResponse:
    """
    Update an existing role.

    Args:
        role_id: Unique identifier of the role.
        payload: Updated role data.
        db: Active database session.

    Returns:
        The updated role.

    Raises:
        HTTPException: If the role does not exist.
    """
    role = role_crud.get(
        db=db,
        role_id=role_id,
    )

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    return role_crud.update(
        db=db,
        role=role,
        payload=payload,
    )


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_role(
    role_id: int,
    db: DBSession,
) -> None:
    """
    Delete a role.

    Args:
        role_id: Unique identifier of the role.
        db: Active database session.

    Raises:
        HTTPException: If the role does not exist.
    """
    role = role_crud.get(
        db=db,
        role_id=role_id,
    )

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    role_crud.delete(
        db=db,
        role=role,
    )
