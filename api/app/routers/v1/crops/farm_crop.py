"""
Farm crop API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.crops.farm_crop import FarmCropRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.crops.farm_crop import FarmCropCreate, FarmCropResponse, FarmCropUpdate
from app.security.dependencies import CurrentActiveUser, require_roles
from app.services.crops.farm_crop import FarmCropService

router = APIRouter(prefix="/farm-crops", tags=["Farm Crops"])

# Admins and Operations Team may write farm crops; farm scope is enforced in the service.
require_farm_crop_write = require_roles("Admin", "Operations Team")


def get_farm_crop_service(
    db: DatabaseSession,
    current_user: CurrentActiveUser,
) -> FarmCropService:
    """Create and return a FarmCrop service instance scoped to the current user."""
    return FarmCropService(FarmCropRepository(db), current_user)


FarmCropServiceDep = Annotated[FarmCropService, Depends(get_farm_crop_service)]


@router.get("", response_model=list[FarmCropResponse])
def list_farm_crops(service: FarmCropServiceDep, pagination: PaginationDep):
    """List farm crop records visible to the current user."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{farm_crop_id}", response_model=FarmCropResponse)
def get_farm_crop(farm_crop_id: int, service: FarmCropServiceDep):
    """Get a farm crop record by ID."""
    return service.get(farm_crop_id)


@router.post(
    "",
    response_model=FarmCropResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_farm_crop_write)],
)
def create_farm_crop(payload: FarmCropCreate, service: FarmCropServiceDep):
    """Create a farm crop record (Admin or Operations Team, own farm)."""
    return service.create(payload)


@router.put(
    "/{farm_crop_id}",
    response_model=FarmCropResponse,
    dependencies=[Depends(require_farm_crop_write)],
)
def update_farm_crop(
    farm_crop_id: int,
    payload: FarmCropUpdate,
    service: FarmCropServiceDep,
):
    """Update a farm crop record by ID (Admin or Operations Team, own farm)."""
    return service.update(farm_crop_id, payload)


@router.delete(
    "/{farm_crop_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_farm_crop_write)],
)
def delete_farm_crop(farm_crop_id: int, service: FarmCropServiceDep):
    """Delete a farm crop record by ID (Admin or Operations Team, own farm)."""
    service.delete(farm_crop_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
