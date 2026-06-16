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
    return role_crud.create(db, payload)


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
)
def get_role(
    role_id: int,
    db: DBSession,
) -> RoleResponse:
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
