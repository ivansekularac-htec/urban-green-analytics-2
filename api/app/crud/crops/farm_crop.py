from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crops.farm_crop import FarmCrop
from app.schemas.crops.farm_crop import FarmCropCreate


def create(
    db: Session,
    payload: FarmCropCreate,
) -> FarmCrop:

    obj = FarmCrop(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    farm_crop_id: int,
) -> FarmCrop | None:

    return db.get(FarmCrop, farm_crop_id)


def get_all(
    db: Session,
) -> list[FarmCrop]:

    return list(db.scalars(select(FarmCrop)).all())
