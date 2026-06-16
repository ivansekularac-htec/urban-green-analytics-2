from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crops.crop_category import CropCategory
from app.schemas.crops.crop_category import CropCategoryCreate


def create(
    db: Session,
    payload: CropCategoryCreate,
) -> CropCategory:
    """
    Create a new crop category.

    Args:
        db: Active database session.
        payload: Crop category data used to create the record.

    Returns:
        The newly created crop category instance.
    """

    obj = CropCategory(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    crop_category_id: int,
) -> CropCategory | None:
    """
    Retrieve a crop category by its ID.

    Args:
        db: Active database session.
        crop_category_id: Unique identifier of the crop category.

    Returns:
        The crop category instance if found, otherwise None.
    """

    return db.get(CropCategory, crop_category_id)


def get_all(
    db: Session,
) -> list[CropCategory]:
    """
    Retrieve all crop categories.

    Args:
        db: Active database session.

    Returns:
        A list of all crop category records.
    """

    return list(db.scalars(select(CropCategory)).all())
