from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.crops.farm_crop import FarmCropCreate, FarmCropResponse, FarmCropUpdate
from app.services.crops import farm_crop as farm_crop_service

router = APIRouter(prefix="/farm-crops", tags=["farm-crops"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[FarmCropResponse])
def get_farm_crops(db: DbSession):
    """List all farm crops."""
    return farm_crop_service.get_farm_crops(db)


@router.get("/{farm_crop_id}", response_model=FarmCropResponse)
def get_farm_crop(farm_crop_id: int, db: DbSession):
    """Retrieve a single farm crop by ID."""
    farm_crop = farm_crop_service.get_farm_crop(db, farm_crop_id)
    if not farm_crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm crop not found")
    return farm_crop


@router.post("/", response_model=FarmCropResponse, status_code=status.HTTP_201_CREATED)
def create_farm_crop(payload: FarmCropCreate, db: DbSession):
    """Create a new farm crop."""
    return farm_crop_service.create_farm_crop(db, payload)


@router.put("/{farm_crop_id}", response_model=FarmCropResponse)
def update_farm_crop(farm_crop_id: int, payload: FarmCropUpdate, db: DbSession):
    """Update an existing farm crop."""
    farm_crop = farm_crop_service.get_farm_crop(db, farm_crop_id)
    if not farm_crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm crop not found")
    return farm_crop_service.update_farm_crop(db, farm_crop, payload)


@router.delete("/{farm_crop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm_crop(farm_crop_id: int, db: DbSession):
    """Delete a farm crop."""
    farm_crop = farm_crop_service.get_farm_crop(db, farm_crop_id)
    if not farm_crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm crop not found")
    farm_crop_service.delete_farm_crop(db, farm_crop)
