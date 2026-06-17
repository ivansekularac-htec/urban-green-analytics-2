from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.crops.crop_category import (
    CropCategoryCreate,
    CropCategoryResponse,
    CropCategoryUpdate,
)
from app.services.crops import crop_category as crop_category_service

router = APIRouter(prefix="/crop-categories", tags=["crop-categories"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[CropCategoryResponse])
def get_crop_categories(db: DbSession):
    """List all crop categories."""
    return crop_category_service.get_crop_categories(db)


@router.get("/{category_id}", response_model=CropCategoryResponse)
def get_crop_category(category_id: int, db: DbSession):
    """Retrieve a single crop category by ID."""
    category = crop_category_service.get_crop_category(db, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop category not found")
    return category


@router.post("/", response_model=CropCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_crop_category(payload: CropCategoryCreate, db: DbSession):
    """Create a new crop category."""
    return crop_category_service.create_crop_category(db, payload)


@router.put("/{category_id}", response_model=CropCategoryResponse)
def update_crop_category(category_id: int, payload: CropCategoryUpdate, db: DbSession):
    """Update an existing crop category."""
    category = crop_category_service.get_crop_category(db, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop category not found")
    return crop_category_service.update_crop_category(db, category, payload)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crop_category(category_id: int, db: DbSession):
    """Delete a crop category."""
    category = crop_category_service.get_crop_category(db, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop category not found")
    crop_category_service.delete_crop_category(db, category)
