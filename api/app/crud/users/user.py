from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users.user import User
from app.schemas.users.user import UserCreate


def create(
    db: Session,
    payload: UserCreate,
) -> User:

    obj = User(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    user_id: int,
) -> User | None:

    return db.get(User, user_id)


def get_all(
    db: Session,
) -> list[User]:

    return list(db.scalars(select(User)).all())
