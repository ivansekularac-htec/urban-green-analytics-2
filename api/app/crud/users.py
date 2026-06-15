from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users.role import Role
from app.schemas.users.role import RoleCreate


def create(
    db: Session,
    payload: RoleCreate,
) -> Role:
    obj = Role(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    role_id: int,
) -> Role | None:
    return db.get(Role, role_id)


def get_all(
    db: Session,
) -> list[Role]:
    return list(db.scalars(select(Role)).all())
