from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.database import DbSession
from app.models.crops.crop_category import CropCategory
from app.schemas.crops.crop import CropUpdate
from app.schemas.crops.crop_category import (
    CropCategoryCreate,
    CropCategoryResponse,
)

crop_categories_router = APIRouter(prefix="/crop_categories", tags=["crop_categories"])


@crop_categories_router.post(
    "/",
    response_model=CropCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_crop_category(
    payload: CropCategoryCreate,
    db: DbSession,
) -> CropCategory:
    crop_category = CropCategory(**payload.model_dump())

    db.add(crop_category)
    db.commit()
    db.refresh(crop_category)

    return crop_category


@crop_categories_router.get(
    "/",
    response_model=list[CropCategoryResponse],
)
def get_crop_categories(
    db: DbSession,
) -> list[CropCategory]:
    return db.scalars(select(CropCategory)).all()


@crop_categories_router.get(
    "/{crop_category_id}",
    response_model=CropCategoryResponse,
)
def get_crop_category(
    crop_category_id: int,
    db: DbSession,
) -> CropCategory:
    crop_category = db.scalar(select(CropCategory).where(CropCategory.id == crop_category_id))

    if crop_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop category not found",
        )

    return crop_category


@crop_categories_router.put(
    "/{crop_category_id}",
    response_model=CropCategoryResponse,
)
def update_crop_category(
    crop_category_id: int,
    payload: CropUpdate,
    db: DbSession,
) -> CropCategory:
    crop_category = db.scalar(select(CropCategory).where(CropCategory.id == crop_category_id))

    if crop_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop category not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(crop_category, field, value)

    db.commit()

    return crop_category


@crop_categories_router.delete(
    "/{crop_category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_crop_category(
    crop_category_id: int,
    db: DbSession,
) -> None:
    crop_category = db.scalar(select(CropCategory).where(CropCategory.id == crop_category_id))

    if crop_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop category not found",
        )

    db.delete(crop_category)
    db.commit()
