"""
Farm API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.farms.farm import FarmRepository
from app.routers.v1.auth.dependencies import (
    CurrentUserDep,
    assert_farm_access,
    can_access_all_farms,
    get_accessible_farm_ids,
)
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.farms.farm import FarmCreate, FarmResponse, FarmUpdate
from app.security.rbac import require_roles
from app.services.farms.farm import FarmService

router = APIRouter(prefix="/farms", tags=["Farms"])


def get_farm_service(db: DatabaseSession) -> FarmService:
    """Create and return a Farm service instance."""
    return FarmService(FarmRepository(db))


FarmServiceDep = Annotated[
    FarmService,
    Depends(get_farm_service),
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
        )
    ),
]


@router.get("", response_model=list[FarmResponse])
def list_farms(
    service: FarmServiceDep,
    pagination: PaginationDep,
    current_user: CurrentUserDep,
    _: ReadDep,
):
    """
    List farms.

    Admin and Operations can see all farms.
    Farm Managers can see only farms assigned to them.
    """
    if can_access_all_farms(current_user):
        return service.list(
            skip=pagination.skip,
            limit=pagination.limit,
        )

    return service.list_by_ids(
        farm_ids=get_accessible_farm_ids(current_user),
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{farm_id}", response_model=FarmResponse)
def get_farm(
    farm_id: int,
    service: FarmServiceDep,
    current_user: CurrentUserDep,
    _: ReadDep,
):
    """
    Get a farm by ID.
    Farm Managers can access only their own farms.
    """
    farm = service.get(farm_id)

    assert_farm_access(
        current_user,
        farm.id,
    )

    return farm


@router.post("", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
def create_farm(
    payload: FarmCreate,
    service: FarmServiceDep,
    _: ManageDep,
):
    """
    Create a farm.
    Only Admin can create farms.
    """

    return service.create(payload)


@router.put("/{farm_id}", response_model=FarmResponse)
def update_farm(
    farm_id: int,
    payload: FarmUpdate,
    service: FarmServiceDep,
    _: ManageDep,
):
    """
    Update a farm.
    Only Admin can update farms.
    """
    return service.update(farm_id, payload)


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm(
    farm_id: int,
    service: FarmServiceDep,
    _: ManageDep,
):
    """
    Delete a farm.
    Only Admin can delete farms.
    """
    service.delete(farm_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
