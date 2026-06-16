from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.users import user as user_crud
from app.database import get_db
from app.schemas.users.user import UserCreate, UserResponse

router = APIRouter(prefix="/v1/user", tags=["User"])

DBSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: UserCreate,
    db: DBSession,
) -> UserResponse:
    return user_crud.create(db, payload)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: DBSession,
) -> UserResponse:
    user = user_crud.get(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user


@router.get(
    "/",
    response_model=list[UserResponse],
)
def get_users(
    db: DBSession,
) -> list[UserResponse]:
    return user_crud.get_all(db)
