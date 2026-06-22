"""
Harvest API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.harvests.harvest import HarvestRepository
from app.routers.v1.auth.dependencies import (
    CurrentUserDep,
    assert_farm_access,
    can_access_all_farms,
    get_accessible_farm_ids,
)
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.harvests.harvest import (
    HarvestCreate,
    HarvestResponse,
    HarvestUpdate,
)
from app.security.rbac import require_roles
from app.services.harvests.harvest import HarvestService

router = APIRouter(
    prefix="/harvests",
    tags=["Harvests"],
)


def get_harvest_service(
    db: DatabaseSession,
) -> HarvestService:
    """Create and return a Harvest service instance."""
    return HarvestService(
        HarvestRepository(db),
    )


HarvestServiceDep = Annotated[
    HarvestService,
    Depends(get_harvest_service),
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


@router.get("", response_model=list[HarvestResponse])
def list_harvests(
    service: HarvestServiceDep,
    pagination: PaginationDep,
    current_user: CurrentUserDep,
    _: ReadDep,
):
    """
    List harvest records.

    Admin and Operations can see all harvests.
    Farm Managers can see only harvests belonging to their farms.
    """

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


@router.get("/{harvest_id}", response_model=HarvestResponse)
def get_harvest(
    harvest_id: int,
    service: HarvestServiceDep,
    current_user: CurrentUserDep,
    _: ReadDep,
):
    """
    Get a harvest record by ID.
    """

    harvest = service.get(harvest_id)

    assert_farm_access(
        current_user,
        harvest.farm_id,
    )

    return harvest


@router.post(
    "",
    response_model=HarvestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_harvest(
    payload: HarvestCreate,
    service: HarvestServiceDep,
    _: ManageDep,
):
    """
    Create a harvest record.
    """

    return service.create(
        payload,
    )


@router.put("/{harvest_id}", response_model=HarvestResponse)
def update_harvest(
    harvest_id: int,
    payload: HarvestUpdate,
    service: HarvestServiceDep,
    _: ManageDep,
):
    """
    Update a harvest record by ID.
    """

    return service.update(
        harvest_id,
        payload,
    )


@router.delete("/{harvest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_harvest(
    harvest_id: int,
    service: HarvestServiceDep,
    _: ManageDep,
):
    """
    Delete a harvest record by ID.
    """

    service.delete(
        harvest_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
