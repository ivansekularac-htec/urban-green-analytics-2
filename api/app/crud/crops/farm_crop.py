from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crops.farm_crop import FarmCrop
from app.schemas.crops.farm_crop import FarmCropCreate, FarmCropUpdate


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


def update(
    db: Session,
    farm_crop: FarmCrop,
    payload: FarmCropUpdate,
) -> FarmCrop:
    """Update an existing farm crop assignment."""

    for field, value in payload.model_dump(
        exclude_unset=True,
    ).items():
        setattr(farm_crop, field, value)

    db.commit()
    db.refresh(farm_crop)

    return farm_crop


def delete(
    db: Session,
    farm_crop: FarmCrop,
) -> None:
    """Delete a farm crop assignment."""

    db.delete(farm_crop)
    db.commit()
