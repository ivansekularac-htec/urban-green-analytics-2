"""
farms.py
API routes for farm management.

This module defines CRUD endpoints for Farm resources.
"""

from fastapi import APIRouter, status

from app.database import SessionDep
from app.models.farms.farm import Farm
from app.models.farms.growing_system_type import GrowingSystemType
from app.models.farms.infrastructure_type import InfrastructureType
from app.schemas.farms.farm import FarmCreate, FarmResponse, FarmUpdate
from app.services.common import get_or_404
from app.services.farms import farm_service

router = APIRouter(
    prefix="/farms",
    tags=["Farms"],
)


@router.post(
    "",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_farm(
    farm_data: FarmCreate,
    db: SessionDep,
) -> FarmResponse:
    """Create a new farm."""
    get_or_404(
        db,
        InfrastructureType,
        farm_data.infrastructure_type_id,
        "Farm infrastructure type",
    )
    get_or_404(
        db,
        GrowingSystemType,
        farm_data.growing_system_type_id,
        "Growing system type",
    )

    return farm_service.create_farm(db, farm_data)


@router.get(
    "",
    response_model=list[FarmResponse],
)
def get_farms(
    db: SessionDep,
) -> list[FarmResponse]:
    """Return all farms."""
    return farm_service.get_farms(db)


@router.get(
    "/{farm_id}",
    response_model=FarmResponse,
)
def get_farm(
    farm_id: int,
    db: SessionDep,
) -> FarmResponse:
    """Return a farm by ID."""
    return get_or_404(db, Farm, farm_id, "Farm")


@router.put(
    "/{farm_id}",
    response_model=FarmResponse,
)
def update_farm(
    farm_id: int,
    farm_data: FarmUpdate,
    db: SessionDep,
) -> FarmResponse:
    """Update a farm by ID."""
    farm = get_or_404(db, Farm, farm_id, "Farm")

    if farm_data.infrastructure_type_id is not None:
        get_or_404(
            db,
            InfrastructureType,
            farm_data.infrastructure_type_id,
            "Farm infrastructure type",
        )

    if farm_data.growing_system_type_id is not None:
        get_or_404(
            db,
            GrowingSystemType,
            farm_data.growing_system_type_id,
            "Growing system type",
        )

    return farm_service.update_farm(db, farm, farm_data)


@router.delete(
    "/{farm_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_farm(
    farm_id: int,
    db: SessionDep,
) -> None:
    """Delete a farm by ID."""
    farm = get_or_404(db, Farm, farm_id, "Farm")

    farm_service.delete_farm(db, farm)
