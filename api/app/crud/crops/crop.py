from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crops.crop import Crop
from app.schemas.crops.crop import CropCreate


def create(
    db: Session,
    payload: CropCreate,
) -> Crop:

    obj = Crop(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    crop_id: int,
) -> Crop | None:

    return db.get(Crop, crop_id)


def get_all(
    db: Session,
) -> list[Crop]:

    return list(db.scalars(select(Crop)).all())
