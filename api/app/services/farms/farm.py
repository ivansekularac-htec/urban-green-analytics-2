from sqlalchemy.orm import Session

from app.models.farms.farm import Farm
from app.schemas.farms.farm import FarmCreate, FarmUpdate


def get_farms(db: Session) -> list[Farm]:
    """Query and return all farms from the database."""
    return db.query(Farm).all()


def get_farm(db: Session, farm_id: int) -> Farm | None:
    """Return a single farm by ID, or None if not found."""
    return db.query(Farm).filter(Farm.id == farm_id).first()


def create_farm(db: Session, payload: FarmCreate) -> Farm:
    """Persist a new farm to the database and return it."""
    farm = Farm(**payload.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


def update_farm(db: Session, farm: Farm, payload: FarmUpdate) -> Farm:
    """Apply partial field updates to an existing farm and return it."""
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(farm, field, value)
    db.commit()
    db.refresh(farm)
    return farm


def delete_farm(db: Session, farm: Farm) -> None:
    """Delete a farm from the database."""
    db.delete(farm)
    db.commit()
