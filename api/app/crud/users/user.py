from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users.user import User
from app.schemas.users.user import UserCreate, UserUpdate

password_hash = PasswordHash.recommended()


def create(
    db: Session,
    payload: UserCreate,
) -> User:

    obj = User(
        **payload.model_dump(exclude={"password"}),
        password_hash=password_hash.hash(payload.password),
    )

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


def update(
    db: Session,
    user: User,
    payload: UserUpdate,
) -> User:

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


def delete(
    db: Session,
    user: User,
) -> None:
    """Delete a user."""

    db.delete(user)
    db.commit()
