"""
Crop API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.crops.crop import CropRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.crops.crop import (
    CropCreate,
    CropResponse,
    CropUpdate,
)
from app.security.rbac import require_roles
from app.services.crops.crop import CropService

router = APIRouter(
    prefix="/crops",
    tags=["Crops"],
)


def get_crop_service(
    db: DatabaseSession,
) -> CropService:
    """
    Create and return a Crop service instance.
    """
    return CropService(
        CropRepository(db),
    )


CropServiceDep = Annotated[
    CropService,
    Depends(get_crop_service),
]


ReadCropsDep = Annotated[
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


@router.get("", response_model=list[CropResponse])
def list_crops(
    service: CropServiceDep,
    pagination: PaginationDep,
    _: ReadCropsDep,
):
    """
    List crop records.
    """
    return service.list(
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{crop_id}", response_model=CropResponse)
def get_crop(
    crop_id: int,
    service: CropServiceDep,
    _: ReadCropsDep,
):
    """
    Get a crop record by ID.
    """
    return service.get(
        crop_id,
    )


@router.post("", response_model=CropResponse, status_code=status.HTTP_201_CREATED)
def create_crop(
    payload: CropCreate,
    service: CropServiceDep,
    _: AdminDep,
):
    """
    Create a crop record.
    """
    return service.create(
        payload,
    )


@router.put("/{crop_id}", response_model=CropResponse)
def update_crop(
    crop_id: int,
    payload: CropUpdate,
    service: CropServiceDep,
    _: AdminDep,
):
    """
    Update a crop record by ID.
    """
    return service.update(
        crop_id,
        payload,
    )


@router.delete("/{crop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crop(
    crop_id: int,
    service: CropServiceDep,
    _: AdminDep,
):
    """
    Delete a crop record by ID.
    """
    service.delete(
        crop_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
