"""
Router for FarmCrop entity.

Manages crop cultivation records on farms.
"""

from fastapi import APIRouter, status

from app.database import DbSession
from app.schemas.crops.farm_crop import (
    FarmCropCreate,
    FarmCropResponse,
    FarmCropUpdate,
)
from app.services.crops.farm_crop import FarmCropService

farm_crop_router = APIRouter(
    prefix="/farm-crops",
    tags=["Farm Crops"],
)

service = FarmCropService()


@farm_crop_router.post(
    "",
    response_model=FarmCropResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_farm_crop(
    payload: FarmCropCreate,
    db: DbSession,
):
    """
    Create a new farm-crop relation.
    """
    return service.create(db, payload)


@farm_crop_router.get("", response_model=list[FarmCropResponse])
def get_farm_crops(
    db: DbSession,
):
    """
    Get all farm-crop records.
    """
    return service.get_all(db)


@farm_crop_router.get("/{farm_crop_id}", response_model=FarmCropResponse)
def get_farm_crop(
    farm_crop_id: int,
    db: DbSession,
):
    """
    Get farm-crop record by ID.
    """
    return service.get(db, farm_crop_id)


@farm_crop_router.put("/{farm_crop_id}", response_model=FarmCropResponse)
def update_farm_crop(
    farm_crop_id: int,
    payload: FarmCropUpdate,
    db: DbSession,
):
    """
    Update farm-crop record.
    """
    return service.update(db, farm_crop_id, payload)
