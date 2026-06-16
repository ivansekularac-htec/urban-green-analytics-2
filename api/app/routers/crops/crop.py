"""
Router for Crop entity.

Exposes REST API endpoints:
- Create crop
- Get all crops
- Get crop by ID
- Update crop
- Delete crop
"""

from fastapi import APIRouter, status

from app.database import DbSession
from app.schemas.crops.crop import (
    CropCreate,
    CropResponse,
    CropUpdate,
)
from app.services.crops.crop import CropService

crop_router = APIRouter(
    prefix="/crops",
    tags=["Crops"],
)

service = CropService()


@crop_router.post(
    "",
    response_model=CropResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_crop(payload: CropCreate, db: DbSession):
    """
    Create a new crop.
    """
    return service.create(db, payload)


@crop_router.get("", response_model=list[CropResponse])
def get_crops(
    db: DbSession,
):
    """
    Get all crops.
    """
    return service.get_all(db)


@crop_router.get("/{crop_id}", response_model=CropResponse)
def get_crop(
    crop_id: int,
    db: DbSession,
):
    """
    Get crop by ID.
    """
    return service.get(db, crop_id)


@crop_router.put("/{crop_id}", response_model=CropResponse)
def update_crop(
    crop_id: int,
    payload: CropUpdate,
    db: DbSession,
):
    """
    Update crop.
    """
    return service.update(db, crop_id, payload)


@crop_router.delete("/{crop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crop(
    crop_id: int,
    db: DbSession,
):
    """
    Delete crop.
    """
    service.delete(db, crop_id)
    return None
