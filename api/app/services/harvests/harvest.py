from sqlalchemy.orm import Session

from app.models.harvests.harvest import Harvest
from app.schemas.harvests.harvest import HarvestCreate, HarvestUpdate


def get_harvests(db: Session) -> list[Harvest]:
    """Query and return all harvests from the database."""
    return db.query(Harvest).all()


def get_harvest(db: Session, harvest_id: int) -> Harvest | None:
    """Return a single harvest by ID, or None if not found."""
    return db.query(Harvest).filter(Harvest.id == harvest_id).first()


def create_harvest(db: Session, payload: HarvestCreate) -> Harvest:
    """Persist a new harvest to the database and return it."""
    harvest = Harvest(**payload.model_dump())
    db.add(harvest)
    db.commit()
    db.refresh(harvest)
    return harvest


def update_harvest(db: Session, harvest: Harvest, payload: HarvestUpdate) -> Harvest:
    """Apply partial field updates to an existing harvest and return it."""
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(harvest, field, value)
    db.commit()
    db.refresh(harvest)
    return harvest


def delete_harvest(db: Session, harvest: Harvest) -> None:
    """Delete a harvest from the database."""
    db.delete(harvest)
    db.commit()
