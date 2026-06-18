"""
Crop API routes.

Reference data — readable by any authenticated user; only Admin can write.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.crops.crop import CropRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.crops.crop import CropCreate, CropResponse, CropUpdate
from app.security.dependencies import get_current_user, require_roles
from app.security.roles import RoleName
from app.services.crops.crop import CropService

router = APIRouter(
    prefix="/crops",
    tags=["Crops"],
    dependencies=[Depends(get_current_user)],
)


def get_crop_service(db: DatabaseSession) -> CropService:
    """Create and return a Crop service instance."""
    return CropService(CropRepository(db))


CropServiceDep = Annotated[CropService, Depends(get_crop_service)]


@router.get("", response_model=list[CropResponse])
def list_crops(service: CropServiceDep, pagination: PaginationDep):
    """List crop records."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{crop_id}", response_model=CropResponse)
def get_crop(crop_id: int, service: CropServiceDep):
    """Get a crop record by ID."""
    return service.get(crop_id)


@router.post(
    "",
    response_model=CropResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
def create_crop(payload: CropCreate, service: CropServiceDep):
    """Create a crop record (Admin only)."""
    return service.create(payload)


@router.put(
    "/{crop_id}",
    response_model=CropResponse,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
def update_crop(crop_id: int, payload: CropUpdate, service: CropServiceDep):
    """Update a crop record by ID (Admin only)."""
    return service.update(crop_id, payload)


@router.delete(
    "/{crop_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
def delete_crop(crop_id: int, service: CropServiceDep):
    """Delete a crop record by ID (Admin only)."""
    service.delete(crop_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
