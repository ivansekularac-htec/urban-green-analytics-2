from sqlalchemy.orm import Session

from app.models.crops.crop import Crop
from app.schemas.crops.crop import CropCreate, CropUpdate


def get_crops(db: Session) -> list[Crop]:
    """Query and return all crops from the database."""
    return db.query(Crop).all()


def get_crop(db: Session, crop_id: int) -> Crop | None:
    """Return a single crop by ID, or None if not found."""
    return db.query(Crop).filter(Crop.id == crop_id).first()


def create_crop(db: Session, payload: CropCreate) -> Crop:
    """Persist a new crop to the database and return it."""
    crop = Crop(**payload.model_dump())
    db.add(crop)
    db.commit()
    db.refresh(crop)
    return crop


def update_crop(db: Session, crop: Crop, payload: CropUpdate) -> Crop:
    """Apply partial field updates to an existing crop and return it."""
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(crop, field, value)
    db.commit()
    db.refresh(crop)
    return crop


def delete_crop(db: Session, crop: Crop) -> None:
    """Delete a crop from the database."""
    db.delete(crop)
    db.commit()
