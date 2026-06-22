"""
Farm crop API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.crops.farm_crop import FarmCropRepository
from app.routers.v1.auth.dependencies import (
    CurrentUserDep,
    assert_farm_access,
    can_access_all_farms,
    get_accessible_farm_ids,
)
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.crops.farm_crop import (
    FarmCropCreate,
    FarmCropResponse,
    FarmCropUpdate,
)
from app.security.rbac import require_roles
from app.services.crops.farm_crop import FarmCropService

router = APIRouter(
    prefix="/farm-crops",
    tags=["Farm Crops"],
)


def get_farm_crop_service(
    db: DatabaseSession,
) -> FarmCropService:
    """Create and return a FarmCrop service instance."""
    return FarmCropService(
        FarmCropRepository(db),
    )


FarmCropServiceDep = Annotated[
    FarmCropService,
    Depends(get_farm_crop_service),
]

ReadDep = Annotated[
    object,
    Depends(
        require_roles(
            "Admin",
            "Operations Team",
            "Farm Manager",
        )
    ),
]

ManageDep = Annotated[
    object,
    Depends(
        require_roles(
            "Admin",
            "Operations Team",
        )
    ),
]


@router.get("", response_model=list[FarmCropResponse])
def list_farm_crops(
    service: FarmCropServiceDep,
    pagination: PaginationDep,
    current_user: CurrentUserDep,
    _: ReadDep,
):
    if can_access_all_farms(current_user):
        return service.list(
            skip=pagination.skip,
            limit=pagination.limit,
        )

    return service.list_by_farm_ids(
        farm_ids=get_accessible_farm_ids(current_user),
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{farm_crop_id}", response_model=FarmCropResponse)
def get_farm_crop(
    farm_crop_id: int,
    service: FarmCropServiceDep,
    current_user: CurrentUserDep,
    _: ReadDep,
):
    farm_crop = service.get(farm_crop_id)

    assert_farm_access(
        current_user,
        farm_crop.farm_id,
    )

    return farm_crop


@router.post("", response_model=FarmCropResponse, status_code=status.HTTP_201_CREATED)
def create_farm_crop(
    payload: FarmCropCreate,
    service: FarmCropServiceDep,
    _: ManageDep,
):
    """
    Create a farm crop record.
    """
    return service.create(
        payload,
    )


@router.put("/{farm_crop_id}", response_model=FarmCropResponse)
def update_farm_crop(
    farm_crop_id: int,
    payload: FarmCropUpdate,
    service: FarmCropServiceDep,
    _: ManageDep,
):
    """
    Update a farm crop record by ID.
    """
    return service.update(
        farm_crop_id,
        payload,
    )


@router.delete("/{farm_crop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm_crop(
    farm_crop_id: int,
    service: FarmCropServiceDep,
    _: ManageDep,
):
    """
    Delete a farm crop record by ID.
    """
    service.delete(
        farm_crop_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
