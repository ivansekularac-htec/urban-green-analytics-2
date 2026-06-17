"""
Harvest API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.harvests.harvest import HarvestRepository
from app.routers.v1.common.pagination import PaginationDep
from app.schemas.harvests.harvest import HarvestCreate, HarvestResponse, HarvestUpdate
from app.services.harvests.harvest import HarvestService

router = APIRouter(prefix="/harvests", tags=["Harvests"])


def get_harvest_service(db: DatabaseSession) -> HarvestService:
    """Create and return a Harvest service instance."""
    return HarvestService(HarvestRepository(db))


HarvestServiceDep = Annotated[HarvestService, Depends(get_harvest_service)]


@router.get("", response_model=list[HarvestResponse])
def list_harvests(service: HarvestServiceDep, pagination: PaginationDep):
    """List harvest records."""
    return service.list(skip=pagination.skip, limit=pagination.limit)


@router.get("/{harvest_id}", response_model=HarvestResponse)
def get_harvest(harvest_id: int, service: HarvestServiceDep):
    """Get a harvest record by ID."""
    return service.get(harvest_id)


@router.post("", response_model=HarvestResponse, status_code=status.HTTP_201_CREATED)
def create_harvest(payload: HarvestCreate, service: HarvestServiceDep):
    """Create a harvest record."""
    return service.create(payload)


@router.put("/{harvest_id}", response_model=HarvestResponse)
def update_harvest(harvest_id: int, payload: HarvestUpdate, service: HarvestServiceDep):
    """Update a harvest record by ID."""
    return service.update(harvest_id, payload)


@router.delete("/{harvest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_harvest(harvest_id: int, service: HarvestServiceDep):
    """Delete a harvest record by ID."""
    service.delete(harvest_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
