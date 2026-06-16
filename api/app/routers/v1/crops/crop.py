"""
crops.py
API routes for crop management.

This module defines CRUD endpoints for Crop resources.
"""

from fastapi import APIRouter, status

from app.database import SessionDep
from app.models.crops.crop import Crop
from app.models.crops.crop_category import CropCategory
from app.schemas.crops.crop import CropCreate, CropResponse, CropUpdate
from app.services.common import get_or_404
from app.services.crops import crop_service

router = APIRouter(
    prefix="/crops",
    tags=["Crops"],
)


@router.post(
    "",
    response_model=CropResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_crop(
    crop_data: CropCreate,
    db: SessionDep,
) -> CropResponse:
    """Create a new crop."""
    get_or_404(db, CropCategory, crop_data.category_id, "Crop category")

    return crop_service.create_crop(db, crop_data)


@router.get(
    "",
    response_model=list[CropResponse],
)
def get_crops(
    db: SessionDep,
) -> list[CropResponse]:
    """Return all crops."""
    return crop_service.get_crops(db)


@router.get(
    "/{crop_id}",
    response_model=CropResponse,
)
def get_crop(
    crop_id: int,
    db: SessionDep,
) -> CropResponse:
    """Return a crop by ID."""
    return get_or_404(db, Crop, crop_id, "Crop")


@router.put(
    "/{crop_id}",
    response_model=CropResponse,
)
def update_crop(
    crop_id: int,
    crop_data: CropUpdate,
    db: SessionDep,
) -> CropResponse:
    """Update a crop by ID."""
    crop = get_or_404(db, Crop, crop_id, "Crop")

    if crop_data.category_id is not None:
        get_or_404(db, CropCategory, crop_data.category_id, "Crop category")

    return crop_service.update_crop(db, crop, crop_data)


@router.delete(
    "/{crop_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_crop(
    crop_id: int,
    db: SessionDep,
) -> None:
    """Delete a crop by ID."""
    crop = get_or_404(db, Crop, crop_id, "Crop")

    crop_service.delete_crop(db, crop)
