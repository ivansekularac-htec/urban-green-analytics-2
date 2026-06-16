from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users.user_roles import UserRole
from app.schemas.users.user_roles import UserRoleCreate, UserRoleUpdate


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


def update(
    db: Session,
    user_role: UserRole,
    payload: UserRoleUpdate,
) -> UserRole:
    """Update an existing user role assignment."""

    for field, value in payload.model_dump(
        exclude_unset=True,
    ).items():
        setattr(user_role, field, value)

    db.commit()
    db.refresh(user_role)

    return user_role


def delete(
    db: Session,
    user_role: UserRole,
) -> None:
    """Delete a user role assignment."""

    db.delete(user_role)
    db.commit()
