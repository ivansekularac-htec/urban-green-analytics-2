"""
Crop API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.crops.crop_repository import CropRepository
from app.schemas.crops.crop import CropCreate, CropResponse, CropUpdate
from app.services.crops.crop_service import CropService

router = APIRouter(prefix="/crops", tags=["Crops"])


def get_crop_service(db: DatabaseSession) -> CropService:
    """Create and return a Crop service instance."""
    return CropService(CropRepository(db))


CropServiceDep = Annotated[CropService, Depends(get_crop_service)]


@router.get("", response_model=list[CropResponse])
def list_crops(service: CropServiceDep, skip: int = 0, limit: int = 100):
    """List crop records."""
    return service.list(skip=skip, limit=limit)


@router.get("/{crop_id}", response_model=CropResponse)
def get_crop(crop_id: int, service: CropServiceDep):
    """Get a crop record by ID."""
    return service.get(crop_id)


@router.post("", response_model=CropResponse, status_code=status.HTTP_201_CREATED)
def create_crop(payload: CropCreate, service: CropServiceDep):
    """Create a crop record."""
    return service.create(payload)


@router.put("/{crop_id}", response_model=CropResponse)
def update_crop(crop_id: int, payload: CropUpdate, service: CropServiceDep):
    """Update a crop record by ID."""
    return service.update(crop_id, payload)


@router.delete("/{crop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crop(crop_id: int, service: CropServiceDep):
    """Delete a crop record by ID."""
    service.delete(crop_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
