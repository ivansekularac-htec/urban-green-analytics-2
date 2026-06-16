from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.farms.farm import Farm
from app.schemas.farms.farm import FarmCreate


def create(
    db: Session,
    payload: FarmCreate,
) -> Farm:

    obj = Farm(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    farm_id: int,
) -> Farm | None:

    return db.get(Farm, farm_id)


def get_all(
    db: Session,
) -> list[Farm]:

    return list(db.scalars(select(Farm)).all())
