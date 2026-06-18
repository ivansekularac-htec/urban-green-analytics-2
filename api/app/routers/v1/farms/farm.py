"""
Farm API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.farms.farm import FarmRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.farms.farm import FarmCreate, FarmResponse, FarmUpdate
from app.security.dependencies import CurrentActiveUser, require_admin
from app.services.farms.farm import FarmService

router = APIRouter(prefix="/farms", tags=["Farms"])


def get_farm_service(db: DatabaseSession, current_user: CurrentActiveUser) -> FarmService:
    """Create and return a Farm service instance scoped to the current user."""
    return FarmService(FarmRepository(db), current_user)


FarmServiceDep = Annotated[FarmService, Depends(get_farm_service)]


@router.get("", response_model=list[FarmResponse])
def list_farms(service: FarmServiceDep, pagination: PaginationDep):
    """List farm records visible to the current user."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{farm_id}", response_model=FarmResponse)
def get_farm(farm_id: int, service: FarmServiceDep):
    """Get a farm record by ID."""
    return service.get(farm_id)


@router.post(
    "",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_farm(payload: FarmCreate, service: FarmServiceDep):
    """Create a farm record (Admin only)."""
    return service.create(payload)


@router.put("/{farm_id}", response_model=FarmResponse, dependencies=[Depends(require_admin)])
def update_farm(farm_id: int, payload: FarmUpdate, service: FarmServiceDep):
    """Update a farm record by ID (Admin only)."""
    return service.update(farm_id, payload)


@router.delete(
    "/{farm_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_farm(farm_id: int, service: FarmServiceDep):
    """Delete a farm record by ID (Admin only)."""
    service.delete(farm_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
