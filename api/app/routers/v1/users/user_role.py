from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UserRole
from app.schemas import UserRoleCreate, UserRoleResponse, UserRoleUpdate

user_role_router = APIRouter(
    prefix="/user-roles",
    tags=["User Roles"],
)


@user_role_router.get(
    "/",
    response_model=list[UserRoleResponse],
)
def get_user_roles(
    db: Session = Depends(get_db),
):
    return db.query(UserRole).all()


@user_role_router.post(
    "/",
    response_model=UserRoleResponse,
    status_code=201,
)
def create_user_role(
    user_role_data: UserRoleCreate,
    db: Session = Depends(get_db),
):
    user_role = UserRole(**user_role_data.model_dump())

    db.add(user_role)
    db.commit()
    db.refresh(user_role)

    return user_role


@user_role_router.put(
    "/{user_role_id}",
    response_model=UserRoleResponse,
)
def update_user_role(
    user_role_id: int,
    user_role_data: UserRoleUpdate,
    db: Session = Depends(get_db),
):
    user_role = db.query(UserRole).filter(UserRole.id == user_role_id).first()

    if user_role is None:
        raise HTTPException(
            status_code=404,
            detail="User role not found",
        )

    for field, value in user_role_data.model_dump(
        exclude_unset=True,
    ).items():
        setattr(user_role, field, value)

    db.commit()
    db.refresh(user_role)

    return user_role


@user_role_router.delete(
    "/{user_role_id}",
    status_code=204,
)
def delete_user_role(
    user_role_id: int,
    db: Session = Depends(get_db),
):
    user_role = db.query(UserRole).filter(UserRole.id == user_role_id).first()

    if user_role is None:
        raise HTTPException(
            status_code=404,
            detail="User role not found",
        )

    db.delete(user_role)
    db.commit()
