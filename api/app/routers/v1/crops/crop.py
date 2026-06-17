from typing import Annotated

from app.services.crops import crop as crop_service
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.crops.crop import CropCreate, CropResponse, CropUpdate

router = APIRouter(prefix="/crops", tags=["crops"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[CropResponse])
def get_crops(db: DbSession):
    """List all crops."""
    return crop_service.get_crops(db)


@router.get("/{crop_id}", response_model=CropResponse)
def get_crop(crop_id: int, db: DbSession):
    """Retrieve a single crop by ID."""
    crop = crop_service.get_crop(db, crop_id)
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop not found")
    return crop


@router.post("/", response_model=CropResponse, status_code=status.HTTP_201_CREATED)
def create_crop(payload: CropCreate, db: DbSession):
    """Create a new crop."""
    return crop_service.create_crop(db, payload)


@router.put("/{crop_id}", response_model=CropResponse)
def update_crop(crop_id: int, payload: CropUpdate, db: DbSession):
    """Update an existing crop."""
    crop = crop_service.get_crop(db, crop_id)
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop not found")
    return crop_service.update_crop(db, crop, payload)


@router.delete("/{crop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crop(crop_id: int, db: DbSession):
    """Delete a crop."""
    crop = crop_service.get_crop(db, crop_id)
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop not found")
    crop_service.delete_crop(db, crop)
