from sqlalchemy.orm import Session

from app.models.crops.farm_crop import FarmCrop
from app.schemas.crops.farm_crop import FarmCropCreate, FarmCropUpdate


def get_farm_crops(db: Session) -> list[FarmCrop]:
    """Query and return all farm crops from the database."""
    return db.query(FarmCrop).all()


def get_farm_crop(db: Session, farm_crop_id: int) -> FarmCrop | None:
    """Return a single farm crop by ID, or None if not found."""
    return db.query(FarmCrop).filter(FarmCrop.id == farm_crop_id).first()


def create_farm_crop(db: Session, payload: FarmCropCreate) -> FarmCrop:
    """Persist a new farm crop to the database and return it."""
    farm_crop = FarmCrop(**payload.model_dump())
    db.add(farm_crop)
    db.commit()
    db.refresh(farm_crop)
    return farm_crop


def update_farm_crop(db: Session, farm_crop: FarmCrop, payload: FarmCropUpdate) -> FarmCrop:
    """Apply partial field updates to an existing farm crop and return it."""
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(farm_crop, field, value)
    db.commit()
    db.refresh(farm_crop)
    return farm_crop


def delete_farm_crop(db: Session, farm_crop: FarmCrop) -> None:
    """Delete a farm crop from the database."""
    db.delete(farm_crop)
    db.commit()
