from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.database import DbSession
from app.models.crops.crop import Crop
from app.schemas.crops.crop import (
    CropCreate,
    CropResponse,
    CropUpdate,
)

crops_router = APIRouter(prefix="/crops", tags=["crops"])


@crops_router.post(
    "/",
    response_model=CropResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_crop(
    payload: CropCreate,
    db: DbSession,
) -> Crop:
    crop = Crop(**payload.model_dump())

    db.add(crop)
    db.commit()
    db.refresh(crop)

    return crop


@crops_router.get(
    "/",
    response_model=list[CropResponse],
)
def get_crops(
    db: DbSession,
) -> list[Crop]:
    return db.scalars(select(Crop)).all()


@crops_router.get(
    "/{crop_id}",
    response_model=CropResponse,
)
def get_crop(
    crop_id: int,
    db: DbSession,
) -> Crop:
    crop = db.scalar(select(Crop).where(Crop.id == crop_id))

    if crop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found",
        )

    return crop


@crops_router.put(
    "/{crop_id}",
    response_model=CropResponse,
)
def update_crop(
    crop_id: int,
    payload: CropUpdate,
    db: DbSession,
) -> Crop:
    crop = db.scalar(select(Crop).where(Crop.id == crop_id))

    if crop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(crop, field, value)

    db.commit()

    return crop


@crops_router.delete(
    "/{crop_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_crop(
    crop_id: int,
    db: DbSession,
) -> None:
    crop = db.scalar(select(Crop).where(Crop.id == crop_id))

    if crop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found",
        )

    db.delete(crop)
    db.commit()
