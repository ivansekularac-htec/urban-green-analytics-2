from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.farms.growing_system_type import GrowingSystemType
from app.schemas.farms.growing_system_type import GrowingSystemTypeCreate


def create(
    db: Session,
    payload: GrowingSystemTypeCreate,
) -> GrowingSystemType:

    obj = GrowingSystemType(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    growing_system_type_id: int,
) -> GrowingSystemType | None:

    return db.get(GrowingSystemType, growing_system_type_id)


def get_all(
    db: Session,
) -> list[GrowingSystemType]:

    return list(db.scalars(select(GrowingSystemType)).all())
