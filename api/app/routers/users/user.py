from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.users import user as user_crud
from app.database import get_db
from app.schemas.users.user import UserCreate, UserResponse, UserUpdate

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


@router.put(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: DBSession,
) -> UserResponse:

    user = user_crud.get(
        db=db,
        user_id=user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user_crud.update(
        db=db,
        user=user,
        payload=payload,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(
    user_id: int,
    db: DBSession,
) -> None:
    """Delete a user."""

    user = user_crud.get(
        db=db,
        user_id=user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user_crud.delete(
        db=db,
        user=user,
    )
