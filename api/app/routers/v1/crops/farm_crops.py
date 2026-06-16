from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.database import DbSession
from app.models.crops.farm_crop import FarmCrop
from app.schemas.crops.farm_crop import (
    FarmCropCreate,
    FarmCropResponse,
    FarmCropUpdate,
)

farm_crops_router = APIRouter(prefix="/farm-crops", tags=["farm-crops"])


@farm_crops_router.post(
    "/",
    response_model=FarmCropResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_farm_crop(
    payload: FarmCropCreate,
    db: DbSession,
) -> FarmCrop:
    farm_crop = FarmCrop(**payload.model_dump())

    db.add(farm_crop)
    db.commit()
    db.refresh(farm_crop)

    return farm_crop


@farm_crops_router.get(
    "/",
    response_model=list[FarmCropResponse],
)
def get_farm_crops(
    db: DbSession,
) -> list[FarmCrop]:
    return db.scalars(select(FarmCrop)).all()


@farm_crops_router.get(
    "/{farm_crop_id}",
    response_model=FarmCropResponse,
)
def get_farm_crop(
    farm_crop_id: int,
    db: DbSession,
) -> FarmCrop:
    farm_crop = db.scalar(select(FarmCrop).where(FarmCrop.id == farm_crop_id))

    if farm_crop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm crop not found",
        )

    return farm_crop


@farm_crops_router.put(
    "/{farm_crop_id}",
    response_model=FarmCropResponse,
)
def update_farm_crop(
    farm_crop_id: int,
    payload: FarmCropUpdate,
    db: DbSession,
) -> FarmCrop:
    farm_crop = db.scalar(select(FarmCrop).where(FarmCrop.id == farm_crop_id))

    if farm_crop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm crop not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(farm_crop, field, value)

    db.commit()

    return farm_crop


@farm_crops_router.delete(
    "/{farm_crop_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_farm_crop(
    farm_crop_id: int,
    db: DbSession,
) -> None:
    farm_crop = db.scalar(select(FarmCrop).where(FarmCrop.id == farm_crop_id))

    if farm_crop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm crop not found",
        )

    db.delete(farm_crop)
    db.commit()
