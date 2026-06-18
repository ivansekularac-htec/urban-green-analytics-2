"""
Farm crop API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.dependencies.auth import (
    FARM_MANAGER_ROLE,
    AdminUserDep,
    FarmReadUserDep,
    require_farm_access,
    user_has_role,
)
from app.repositories.crops.farm_crop import FarmCropRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.crops.farm_crop import FarmCropCreate, FarmCropResponse, FarmCropUpdate
from app.services.crops.farm_crop import FarmCropService

router = APIRouter(prefix="/farm-crops", tags=["Farm Crops"])


def get_farm_crop_service(db: DatabaseSession) -> FarmCropService:
    """Create and return a FarmCrop service instance."""
    return FarmCropService(FarmCropRepository(db))


FarmCropServiceDep = Annotated[FarmCropService, Depends(get_farm_crop_service)]


@router.get("", response_model=list[FarmCropResponse])
def list_farm_crops(
    service: FarmCropServiceDep, pagination: PaginationDep, current_user: AdminUserDep
):
    """List farm crop records."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{farm_crop_id}", response_model=FarmCropResponse)
def get_farm_crop(farm_crop_id: int, service: FarmCropServiceDep, current_user: FarmReadUserDep):
    """Get a farm crop record by ID."""
    farm_crop = service.get(farm_crop_id)

    if user_has_role(current_user, FARM_MANAGER_ROLE):
        require_farm_access(
            current_user,
            farm_crop.farm_id,
        )

    return farm_crop


@router.post("", response_model=FarmCropResponse, status_code=status.HTTP_201_CREATED)
def create_farm_crop(
    payload: FarmCropCreate, service: FarmCropServiceDep, current_user: AdminUserDep
):
    """Create a farm crop record."""
    return service.create(payload)


@router.put("/{farm_crop_id}", response_model=FarmCropResponse)
def update_farm_crop(
    farm_crop_id: int,
    payload: FarmCropUpdate,
    service: FarmCropServiceDep,
    current_user: AdminUserDep,
):
    """Update a farm crop record by ID."""
    return service.update(farm_crop_id, payload)


@router.delete("/{farm_crop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm_crop(farm_crop_id: int, service: FarmCropServiceDep, current_user: AdminUserDep):
    """Delete a farm crop record by ID."""
    service.delete(farm_crop_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
