"""
Crop category API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.crops.crop_category_repository import CropCategoryRepository
from app.schemas.crops.crop_category import (
    CropCategoryCreate,
    CropCategoryResponse,
    CropCategoryUpdate,
)
from app.services.crops.crop_category_service import CropCategoryService

router = APIRouter(prefix="/crop-categories", tags=["Crop Categories"])


def get_crop_category_service(db: DatabaseSession) -> CropCategoryService:
    """Create and return a CropCategory service instance."""
    return CropCategoryService(CropCategoryRepository(db))


CropCategoryServiceDep = Annotated[CropCategoryService, Depends(get_crop_category_service)]


@router.get("", response_model=list[CropCategoryResponse])
def list_crop_categories(service: CropCategoryServiceDep, skip: int = 0, limit: int = 100):
    """List crop category records."""
    return service.list(skip=skip, limit=limit)


@router.get("/{crop_category_id}", response_model=CropCategoryResponse)
def get_crop_category(crop_category_id: int, service: CropCategoryServiceDep):
    """Get a crop category record by ID."""
    return service.get(crop_category_id)


@router.post("", response_model=CropCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_crop_category(payload: CropCategoryCreate, service: CropCategoryServiceDep):
    """Create a crop category record."""
    return service.create(payload)


@router.put("/{crop_category_id}", response_model=CropCategoryResponse)
def update_crop_category(
    crop_category_id: int,
    payload: CropCategoryUpdate,
    service: CropCategoryServiceDep,
):
    """Update a crop category record by ID."""
    return service.update(crop_category_id, payload)


@router.delete("/{crop_category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crop_category(crop_category_id: int, service: CropCategoryServiceDep):
    """Delete a crop category record by ID."""
    service.delete(crop_category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
