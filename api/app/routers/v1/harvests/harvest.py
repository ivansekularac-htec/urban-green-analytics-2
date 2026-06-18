# """
# Harvest API routes.
# """

# from typing import Annotated

# from fastapi import APIRouter, Depends, Response, status

# from app.database import DatabaseSession
# from app.models.users.user import User
# from app.repositories.harvests.harvest import HarvestRepository
# from app.routers.v1.auth.dependencies import (
#     CurrentUserDep,
#     assert_can_read_harvests,
#     assert_harvest_read_access,
#     require_operations_or_admin,
# )
# from app.routers.v1.common.pagination import PaginationDep
# from app.schemas.harvests.harvest import HarvestCreate, HarvestResponse, HarvestUpdate
# from app.services.harvests.harvest import HarvestService

# router = APIRouter(prefix="/harvests", tags=["Harvests"])


# def get_harvest_service(db: DatabaseSession) -> HarvestService:
#     """Create and return a Harvest service instance."""
#     return HarvestService(HarvestRepository(db))


# HarvestServiceDep = Annotated[HarvestService, Depends(get_harvest_service)]


# @router.get("", response_model=list[HarvestResponse])
# def list_harvests(
#     service: HarvestServiceDep,
#     current_user: CurrentUserDep,
#     pagination: PaginationDep,
#     farm_id: int | None = None,
# ):
#     """List harvest records.

#     - Admin/Operations: Can list all harvests, or filter by farm_id
#     - Farm Manager: Must provide farm_id and can only see their farm's harvests
#     """
#     assert_can_read_harvests(current_user)

#     if farm_id is not None:
#         assert_harvest_read_access(current_user, farm_id)
#         return service.list_by_farm(farm_id=farm_id, skip=pagination.skip, limit=pagination.limit)

#     # Admin/Operations can list all
#     return service.list(skip=pagination.skip, limit=pagination.limit)


# @router.get("/{harvest_id}", response_model=HarvestResponse)
# def get_harvest(harvest_id: int, current_user: CurrentUserDep, service: HarvestServiceDep):
#     """Get a harvest record by ID.

#     - Admin/Operations: Can read any harvest
#     - Farm Manager: Can only read harvests from their farm
#     """
#     assert_can_read_harvests(current_user)
#     harvest = service.get(harvest_id)
#     assert_harvest_read_access(current_user, harvest.farm_id)
#     return harvest


# @router.post(
#     "",
#     response_model=HarvestResponse,
#     status_code=status.HTTP_201_CREATED,
# )
# def create_harvest(
#     payload: HarvestCreate,
#     service: HarvestServiceDep,
#     user: Annotated[User, Depends(require_operations_or_admin)],
# ):
#     """Create a harvest record (Operations or Admin only)."""
#     return service.create(payload)


# @router.put("/{harvest_id}", response_model=HarvestResponse)
# def update_harvest(
#     harvest_id: int,
#     payload: HarvestUpdate,
#     service: HarvestServiceDep,
#     user: Annotated[User, Depends(require_operations_or_admin)],
# ):
#     """Update a harvest record by ID (Operations or Admin only)."""
#     return service.update(harvest_id, payload)


# @router.delete("/{harvest_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_harvest(
#     harvest_id: int,
#     service: HarvestServiceDep,
#     user: Annotated[User, Depends(require_operations_or_admin)],
# ):
#     """Delete a harvest record by ID (Operations or Admin only)."""
#     service.delete(harvest_id)
#     return Response(status_code=status.HTTP_204_NO_CONTENT)


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
    is_admin,
    is_operations,
    user_farm_ids,
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

ReadHarvestsDep = Annotated[
    object,
    Depends(
        require_roles(
            "Admin",
            "Operations",
            "Farm Manager",
        )
    ),
]

ManageHarvestsDep = Annotated[
    object,
    Depends(
        require_roles(
            "Admin",
            "Operations",
        )
    ),
]


@router.get("", response_model=list[HarvestResponse])
def list_harvests(
    service: HarvestServiceDep,
    pagination: PaginationDep,
    current_user: CurrentUserDep,
    _: ReadHarvestsDep,
):
    """
    List harvest records.

    Admin and Operations can see all harvests.
    Farm Managers can see only harvests belonging to their farms.
    """

    if is_admin(current_user) or is_operations(current_user):
        return service.list(
            skip=pagination.skip,
            limit=pagination.limit,
        )

    return service.list_by_farm_ids(
        farm_ids=user_farm_ids(current_user),
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{harvest_id}", response_model=HarvestResponse)
def get_harvest(
    harvest_id: int,
    service: HarvestServiceDep,
    current_user: CurrentUserDep,
    _: ReadHarvestsDep,
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
    _: ManageHarvestsDep,
):
    """
    Create a harvest record.
    """
    return service.create(payload)


@router.put("/{harvest_id}", response_model=HarvestResponse)
def update_harvest(
    harvest_id: int,
    payload: HarvestUpdate,
    service: HarvestServiceDep,
    _: ManageHarvestsDep,
):
    """
    Update a harvest record by ID.
    """
    return service.update(harvest_id, payload)


@router.delete("/{harvest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_harvest(
    harvest_id: int,
    service: HarvestServiceDep,
    _: ManageHarvestsDep,
):
    """
    Delete a harvest record by ID.
    """
    service.delete(harvest_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
