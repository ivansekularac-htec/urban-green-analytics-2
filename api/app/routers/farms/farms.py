"""
Farm API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.database import DatabaseSession
from app.repositories.farms.farm_repository import FarmRepository
from app.schemas.farms.farm import FarmCreate, FarmResponse, FarmUpdate
from app.services.farms.farm_service import FarmService

router = APIRouter(prefix="/farms", tags=["Farms"])


def get_farm_service(db: DatabaseSession) -> FarmService:
    """Create and return a Farm service instance."""
    return FarmService(FarmRepository(db))


FarmServiceDep = Annotated[FarmService, Depends(get_farm_service)]


@router.get("", response_model=list[FarmResponse])
def list_farms(service: FarmServiceDep, skip: int = 0, limit: int = 100):
    """List farm records."""
    return service.list(skip=skip, limit=limit)


@router.get("/{farm_id}", response_model=FarmResponse)
def get_farm(farm_id: int, service: FarmServiceDep):
    """Get a farm record by ID."""
    return service.get(farm_id)


@router.post("", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
def create_farm(payload: FarmCreate, service: FarmServiceDep):
    """Create a farm record."""
    return service.create(payload)


@router.put("/{farm_id}", response_model=FarmResponse)
def update_farm(farm_id: int, payload: FarmUpdate, service: FarmServiceDep):
    """Update a farm record by ID."""
    return service.update(farm_id, payload)


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm(farm_id: int, service: FarmServiceDep):
    """Delete a farm record by ID."""
    service.delete(farm_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
