from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, UserUpdate

user_router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@user_router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@user_router.post(
    "/",
    response_model=UserResponse,
    status_code=201,
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        is_active=user_data.is_active,
        password_hash=user_data.password,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@user_router.put(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    for field, value in user_data.model_dump(
        exclude_unset=True,
    ).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user
