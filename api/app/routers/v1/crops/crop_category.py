"""
Crop category API routes.
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
from app.security.rbac import require_roles
from app.services.crops.crop_category import CropCategoryService

router = APIRouter(
    prefix="/crop-categories",
    tags=["Crop Categories"],
)


def get_crop_category_service(
    db: DatabaseSession,
) -> CropCategoryService:
    return CropCategoryService(
        CropCategoryRepository(db),
    )


CropCategoryServiceDep = Annotated[
    CropCategoryService,
    Depends(get_crop_category_service),
]


ReadCropCategoriesDep = Annotated[
    object,
    Depends(
        require_roles(
            "Admin",
            "Operations",
            "Farm Manager",
        )
    ),
]

AdminDep = Annotated[
    object,
    Depends(
        require_roles(
            "Admin",
        )
    ),
]


@router.get("", response_model=list[CropCategoryResponse])
def list_crop_categories(
    service: CropCategoryServiceDep,
    pagination: PaginationDep,
    _: ReadCropCategoriesDep,
):
    """List crop category records."""
    return service.list(
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{crop_category_id}", response_model=CropCategoryResponse)
def get_crop_category(
    crop_category_id: int,
    service: CropCategoryServiceDep,
    _: ReadCropCategoriesDep,
):
    """Get a crop category record by ID."""
    return service.get(
        crop_category_id,
    )


@router.post("", response_model=CropCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_crop_category(
    payload: CropCategoryCreate,
    service: CropCategoryServiceDep,
    _: AdminDep,
):
    """Create a crop category record."""
    return service.create(
        payload,
    )


@router.put("/{crop_category_id}", response_model=CropCategoryResponse)
def update_crop_category(
    crop_category_id: int,
    payload: CropCategoryUpdate,
    service: CropCategoryServiceDep,
    _: AdminDep,
):
    """Update a crop category record by ID."""
    return service.update(
        crop_category_id,
        payload,
    )


@router.delete("/{crop_category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crop_category(
    crop_category_id: int,
    service: CropCategoryServiceDep,
    _: AdminDep,
):
    """Delete a crop category record by ID."""
    service.delete(
        crop_category_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
