from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.harvests.harvest import Harvest
from app.schemas.harvests.harvest import HarvestCreate, HarvestUpdate


def create(
    db: Session,
    payload: HarvestCreate,
) -> Harvest:

    obj = Harvest(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    harvest_id: int,
) -> Harvest | None:

    return db.get(Harvest, harvest_id)


def get_all(
    db: Session,
) -> list[Harvest]:

    return list(db.scalars(select(Harvest)).all())


def update(
    db: Session,
    harvest: Harvest,
    payload: HarvestUpdate,
) -> Harvest:
    """Update an existing harvest."""

    for field, value in payload.model_dump(
        exclude_unset=True,
    ).items():
        setattr(harvest, field, value)

    db.commit()
    db.refresh(harvest)

    return harvest


def delete(
    db: Session,
    harvest: Harvest,
) -> None:
    """Delete a harvest."""

    db.delete(harvest)
    db.commit()
