from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.users import role as role_crud
from app.database import get_db
from app.schemas.users.role import RoleCreate, RoleResponse

router = APIRouter(prefix="/v1/role", tags=["Role"])

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
