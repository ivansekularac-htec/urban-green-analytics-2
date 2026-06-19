"""
Crop category API routes.

Reference data — readable by any authenticated user; only Admin can write.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.crops.crop_category import CropCategoryRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.crops.crop_category import (
    CropCategoryCreate,
    CropCategoryResponse,
    CropCategoryUpdate,
)
from app.security.dependencies import get_current_user, require_roles
from app.security.roles import RoleName
from app.services.crops.crop_category import CropCategoryService

router = APIRouter(
    prefix="/crop-categories",
    tags=["Crop Categories"],
    dependencies=[Depends(get_current_user)],
)


def get_crop_category_service(db: DatabaseSession) -> CropCategoryService:
    """Create and return a CropCategory service instance."""
    return CropCategoryService(CropCategoryRepository(db))


CropCategoryServiceDep = Annotated[CropCategoryService, Depends(get_crop_category_service)]


@router.get("", response_model=list[CropCategoryResponse])
def list_crop_categories(service: CropCategoryServiceDep, pagination: PaginationDep):
    """List crop category records."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{crop_category_id}", response_model=CropCategoryResponse)
def get_crop_category(crop_category_id: int, service: CropCategoryServiceDep):
    """Get a crop category record by ID."""
    return service.get(crop_category_id)


@router.post(
    "",
    response_model=CropCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
def create_crop_category(payload: CropCategoryCreate, service: CropCategoryServiceDep):
    """Create a crop category record (Admin only)."""
    return service.create(payload)


@router.put(
    "/{crop_category_id}",
    response_model=CropCategoryResponse,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
def update_crop_category(
    crop_category_id: int,
    payload: CropCategoryUpdate,
    service: CropCategoryServiceDep,
):
    """Update a crop category record by ID (Admin only)."""
    return service.update(crop_category_id, payload)


@router.delete(
    "/{crop_category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
def delete_crop_category(crop_category_id: int, service: CropCategoryServiceDep):
    """Delete a crop category record by ID (Admin only)."""
    service.delete(crop_category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
