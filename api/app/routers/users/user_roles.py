from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.users import role as user_role_crud
from app.database import get_db
from app.schemas.users.user_roles import UserRoleCreate, UserRoleResponse

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
    return user_role_crud.create(db, payload)


@router.get(
    "/{user_role_id}",
    response_model=UserRoleResponse,
)
def get_user_role(
    user_role_id: int,
    db: DBSession,
) -> UserRoleResponse:
    role = user_role_crud.get(db, user_role_id)

    if user_role_id is None:
        raise HTTPException(
            status_code=404,
            detail="User Role not found",
        )

    return role


@router.get(
    "/",
    response_model=list[UserRoleResponse],
)
def get_user_roles(
    db: DBSession,
) -> list[UserRoleResponse]:
    return user_role_crud.get_all(db)
