from typing import Annotated

from app.services.farms import farm as farm_service
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.farms.farm import FarmCreate, FarmResponse, FarmUpdate

router = APIRouter(prefix="/farms", tags=["farms"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[FarmResponse])
def get_farms(db: DbSession):
    """List all farms."""
    return farm_service.get_farms(db)


@router.get("/{farm_id}", response_model=FarmResponse)
def get_farm(farm_id: int, db: DbSession):
    """Retrieve a single farm by ID."""
    farm = farm_service.get_farm(db, farm_id)
    if not farm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")
    return farm


@router.post("/", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
def create_farm(payload: FarmCreate, db: DbSession):
    """Create a new farm."""
    return farm_service.create_farm(db, payload)


@router.put("/{farm_id}", response_model=FarmResponse)
def update_farm(farm_id: int, payload: FarmUpdate, db: DbSession):
    """Update an existing farm."""
    farm = farm_service.get_farm(db, farm_id)
    if not farm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")
    return farm_service.update_farm(db, farm, payload)


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm(farm_id: int, db: DbSession):
    """Delete a farm."""
    farm = farm_service.get_farm(db, farm_id)
    if not farm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")
    farm_service.delete_farm(db, farm)
