"""
farm_crops.py
API routes for farm crop management.

This module defines CRUD endpoints for FarmCrop resources.
"""

from fastapi import APIRouter, status

from app.database import SessionDep
from app.models.crops.crop import Crop
from app.models.crops.farm_crop import FarmCrop
from app.models.farms.farm import Farm
from app.schemas.crops.farm_crop import FarmCropCreate, FarmCropResponse, FarmCropUpdate
from app.services.common import get_or_404
from app.services.crops import farm_crop_service

router = APIRouter(
    prefix="/farm-crops",
    tags=["Farm Crops"],
)


@router.post("", response_model=FarmCropResponse, status_code=status.HTTP_201_CREATED)
def create_farm_crop(farm_crop_data: FarmCropCreate, db: SessionDep) -> FarmCropResponse:
    """Create a new farm crop assignment."""
    get_or_404(db, Farm, farm_crop_data.farm_id, "Farm")
    get_or_404(db, Crop, farm_crop_data.crop_id, "Crop")

    return farm_crop_service.create_farm_crop(db, farm_crop_data)


@router.get("", response_model=list[FarmCropResponse])
def get_farm_crops(db: SessionDep) -> list[FarmCropResponse]:
    """Return all farm crop assignments."""
    return farm_crop_service.get_farm_crops(db)


@router.get("/{farm_crop_id}", response_model=FarmCropResponse)
def get_farm_crop(farm_crop_id: int, db: SessionDep) -> FarmCropResponse:
    """Return a farm crop assignment by ID."""
    return get_or_404(db, FarmCrop, farm_crop_id, "Farm crop")


@router.put("/{farm_crop_id}", response_model=FarmCropResponse)
def update_farm_crop(
    farm_crop_id: int,
    farm_crop_data: FarmCropUpdate,
    db: SessionDep,
) -> FarmCropResponse:
    """Update a farm crop assignment by ID."""
    farm_crop = get_or_404(db, FarmCrop, farm_crop_id, "Farm crop")

    return farm_crop_service.update_farm_crop(db, farm_crop, farm_crop_data)


@router.delete("/{farm_crop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm_crop(farm_crop_id: int, db: SessionDep) -> None:
    """Delete a farm crop assignment by ID."""
    farm_crop = get_or_404(db, FarmCrop, farm_crop_id, "Farm crop")

    farm_crop_service.delete_farm_crop(db, farm_crop)
