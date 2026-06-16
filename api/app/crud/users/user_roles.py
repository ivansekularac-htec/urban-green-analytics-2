from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users.user_roles import UserRole
from app.schemas.users.user_roles import UserRoleCreate


def create(
    db: Session,
    payload: UserRoleCreate,
) -> UserRole:

    obj = UserRole(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    user_role_id: int,
) -> UserRole | None:

    return db.get(UserRole, user_role_id)


def get_all(
    db: Session,
) -> list[UserRole]:

    return list(db.scalars(select(UserRole)).all())
