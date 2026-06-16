from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crops.crop_category import CropCategory
from app.schemas.crops.crop_category import CropCategoryCreate


def create(
    db: Session,
    payload: CropCategoryCreate,
) -> CropCategory:

    obj = CropCategory(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    crop_category_id: int,
) -> CropCategory | None:

    return db.get(CropCategory, crop_category_id)


def get_all(
    db: Session,
) -> list[CropCategory]:

    return list(db.scalars(select(CropCategory)).all())
