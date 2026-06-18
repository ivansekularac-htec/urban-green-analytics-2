"""
Farm crop API routes.

Read access is open to all authenticated roles, scoped to the farms the
user is assigned to (Admin sees everything). Writes are Admin only.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.crops.farm_crop import FarmCropRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.crops.farm_crop import FarmCropCreate, FarmCropResponse, FarmCropUpdate
from app.security.dependencies import (
    AccessibleFarms,
    assert_farm_in_scope,
    get_current_user,
    require_roles,
)
from app.security.roles import RoleName
from app.services.crops.farm_crop import FarmCropService

router = APIRouter(
    prefix="/farm-crops",
    tags=["Farm Crops"],
    dependencies=[Depends(get_current_user)],
)


def get_farm_crop_service(db: DatabaseSession) -> FarmCropService:
    """Create and return a FarmCrop service instance."""
    return FarmCropService(FarmCropRepository(db))


FarmCropServiceDep = Annotated[FarmCropService, Depends(get_farm_crop_service)]


@router.get("", response_model=list[FarmCropResponse])
def list_farm_crops(service: FarmCropServiceDep, pagination: PaginationDep, farms: AccessibleFarms):
    """List farm crop records visible to the current user."""
    return service.list(skip=pagination.skip, limit=pagination.limit, farm_ids=farms)


@router.get("/{farm_crop_id}", response_model=FarmCropResponse)
def get_farm_crop(farm_crop_id: int, service: FarmCropServiceDep, farms: AccessibleFarms):
    """Get a farm crop record by ID, scoped to the user's farms."""
    farm_crop = service.get(farm_crop_id)
    assert_farm_in_scope(farm_crop.farm_id, farms)
    return farm_crop


@router.post(
    "",
    response_model=FarmCropResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
def create_farm_crop(payload: FarmCropCreate, service: FarmCropServiceDep):
    """Create a farm crop record (Admin only)."""
    return service.create(payload)


@router.put(
    "/{farm_crop_id}",
    response_model=FarmCropResponse,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
def update_farm_crop(
    farm_crop_id: int,
    payload: FarmCropUpdate,
    service: FarmCropServiceDep,
):
    """Update a farm crop record by ID (Admin only)."""
    return service.update(farm_crop_id, payload)


@router.delete(
    "/{farm_crop_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
def delete_farm_crop(farm_crop_id: int, service: FarmCropServiceDep):
    """Delete a farm crop record by ID (Admin only)."""
    service.delete(farm_crop_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
