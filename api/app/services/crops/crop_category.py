from sqlalchemy.orm import Session

from app.models.crops.crop_category import CropCategory
from app.schemas.crops.crop_category import CropCategoryCreate, CropCategoryUpdate


def get_crop_categories(db: Session) -> list[CropCategory]:
    """Query and return all crop categories from the database."""
    return db.query(CropCategory).all()


def get_crop_category(db: Session, category_id: int) -> CropCategory | None:
    """Return a single crop category by ID, or None if not found."""
    return db.query(CropCategory).filter(CropCategory.id == category_id).first()


def create_crop_category(db: Session, payload: CropCategoryCreate) -> CropCategory:
    """Persist a new crop category to the database and return it."""
    category = CropCategory(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_crop_category(
    db: Session, category: CropCategory, payload: CropCategoryUpdate
) -> CropCategory:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category


def delete_crop_category(db: Session, category: CropCategory) -> None:
    """Delete a crop category from the database."""
    db.delete(category)
    db.com
