"""
crop_categories.py
API routes for crop category management.

This module defines CRUD endpoints for CropCategory resources.
"""

from fastapi import APIRouter, status

from app.database import SessionDep
from app.models.crops.crop_category import CropCategory
from app.schemas.crops.crop_category import (
    CropCategoryCreate,
    CropCategoryResponse,
    CropCategoryUpdate,
)
from app.services.common import get_or_404
from app.services.crops import crop_category_service

router = APIRouter(
    prefix="/crop-categories",
    tags=["Crop Categories"],
)


@router.post(
    "",
    response_model=CropCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_crop_category(
    crop_category_data: CropCategoryCreate,
    db: SessionDep,
) -> CropCategoryResponse:
    """Create a new crop category."""
    return crop_category_service.create_crop_category(
        db,
        crop_category_data,
    )


@router.get(
    "",
    response_model=list[CropCategoryResponse],
)
def get_crop_categories(
    db: SessionDep,
) -> list[CropCategoryResponse]:
    """Return all crop categories."""
    return crop_category_service.get_crop_categories(db)


@router.get(
    "/{crop_category_id}",
    response_model=CropCategoryResponse,
)
def get_crop_category(
    crop_category_id: int,
    db: SessionDep,
) -> CropCategoryResponse:
    """Return a crop category by ID."""
    return get_or_404(
        db,
        CropCategory,
        crop_category_id,
        "Crop category",
    )


@router.put(
    "/{crop_category_id}",
    response_model=CropCategoryResponse,
)
def update_crop_category(
    crop_category_id: int,
    crop_category_data: CropCategoryUpdate,
    db: SessionDep,
) -> CropCategoryResponse:
    """Update a crop category by ID."""
    crop_category = get_or_404(
        db,
        CropCategory,
        crop_category_id,
        "Crop category",
    )

    return crop_category_service.update_crop_category(
        db,
        crop_category,
        crop_category_data,
    )


@router.delete(
    "/{crop_category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_crop_category(
    crop_category_id: int,
    db: SessionDep,
) -> None:
    """Delete a crop category by ID."""
    crop_category = get_or_404(
        db,
        CropCategory,
        crop_category_id,
        "Crop category",
    )

    crop_category_service.delete_crop_category(
        db,
        crop_category,
    )
