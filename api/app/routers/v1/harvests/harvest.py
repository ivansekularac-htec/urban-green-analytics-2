"""
Harvest API routes.

Read access is open to all authenticated roles, scoped to the farms the
user is assigned to (Admin sees everything). Writes are Admin or
Operations Team — Operations Team only on farms they're assigned to.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.models.users.user import User
from app.repositories.harvests.harvest import HarvestRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.harvests.harvest import HarvestCreate, HarvestResponse, HarvestUpdate
from app.security.dependencies import (
    AccessibleFarms,
    assert_farm_access,
    assert_farm_in_scope,
    get_current_user,
    require_roles,
)
from app.security.roles import RoleName
from app.services.harvests.harvest import HarvestService

router = APIRouter(
    prefix="/harvests",
    tags=["Harvests"],
    dependencies=[Depends(get_current_user)],
)


def get_harvest_service(db: DatabaseSession) -> HarvestService:
    """Create and return a Harvest service instance."""
    return HarvestService(HarvestRepository(db))


HarvestServiceDep = Annotated[HarvestService, Depends(get_harvest_service)]

# Either an Admin or an Operations Team member can write harvests; the
# specific farm is then enforced by ``assert_farm_access`` inside the route.
HarvestWriter = Annotated[
    User,
    Depends(require_roles(RoleName.ADMIN, RoleName.OPERATIONS_TEAM)),
]


@router.get("", response_model=list[HarvestResponse])
def list_harvests(service: HarvestServiceDep, pagination: PaginationDep, farms: AccessibleFarms):
    """List harvest records visible to the current user."""
    return service.list(skip=pagination.skip, limit=pagination.limit, farm_ids=farms)


@router.get("/{harvest_id}", response_model=HarvestResponse)
def get_harvest(harvest_id: int, service: HarvestServiceDep, farms: AccessibleFarms):
    """Get a harvest record by ID, scoped to the user's farms."""
    harvest = service.get(harvest_id)
    assert_farm_in_scope(harvest.farm_id, farms)
    return harvest


@router.post("", response_model=HarvestResponse, status_code=status.HTTP_201_CREATED)
def create_harvest(payload: HarvestCreate, service: HarvestServiceDep, user: HarvestWriter):
    """Create a harvest record (Admin or Operations Team on their farm)."""
    assert_farm_access(user, payload.farm_id, (RoleName.OPERATIONS_TEAM,))
    return service.create(payload)


@router.put("/{harvest_id}", response_model=HarvestResponse)
def update_harvest(
    harvest_id: int,
    payload: HarvestUpdate,
    service: HarvestServiceDep,
    user: HarvestWriter,
):
    """Update a harvest record by ID (Admin or Operations Team on its farm)."""
    harvest = service.get(harvest_id)
    assert_farm_access(user, harvest.farm_id, (RoleName.OPERATIONS_TEAM,))
    return service.update(harvest_id, payload)


@router.delete("/{harvest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_harvest(harvest_id: int, service: HarvestServiceDep, user: HarvestWriter):
    """Delete a harvest record by ID (Admin or Operations Team on its farm)."""
    harvest = service.get(harvest_id)
    assert_farm_access(user, harvest.farm_id, (RoleName.OPERATIONS_TEAM,))
    service.delete(harvest_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
