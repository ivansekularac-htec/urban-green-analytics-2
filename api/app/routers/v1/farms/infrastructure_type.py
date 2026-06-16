"""
farm_infrastructure_types.py
API routes for farm infrastructure type management.

This module defines CRUD endpoints for FarmInfrastructureType resources.
"""

from fastapi import APIRouter, status

from app.database import SessionDep
from app.models.farms.infrastructure_type import InfrastructureType
from app.schemas.farms.infrastructure_type import (
    InfrastructureTypeCreate,
    InfrastructureTypeResponse,
    InfrastructureTypeUpdate,
)
from app.services.common import get_or_404
from app.services.farms import infrastructure_type_service

router = APIRouter(
    prefix="/farm-infrastructure-types",
    tags=["Farm Infrastructure Types"],
)


@router.post(
    "",
    response_model=InfrastructureTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_farm_infrastructure_type(
    infrastructure_type_data: InfrastructureTypeCreate,
    db: SessionDep,
) -> InfrastructureTypeResponse:
    """Create a new farm infrastructure type."""
    return infrastructure_type_service.create_farm_infrastructure_type(
        db,
        infrastructure_type_data,
    )


@router.get(
    "",
    response_model=list[InfrastructureTypeResponse],
)
def get_farm_infrastructure_types(
    db: SessionDep,
) -> list[InfrastructureTypeResponse]:
    """Return all farm infrastructure types."""
    return infrastructure_type_service.get_farm_infrastructure_types(db)


@router.get(
    "/{infrastructure_type_id}",
    response_model=InfrastructureTypeResponse,
)
def get_farm_infrastructure_type(
    infrastructure_type_id: int,
    db: SessionDep,
) -> InfrastructureTypeResponse:
    """Return a farm infrastructure type by ID."""
    return get_or_404(
        db,
        InfrastructureType,
        infrastructure_type_id,
        "Farm infrastructure type",
    )


@router.put(
    "/{infrastructure_type_id}",
    response_model=InfrastructureTypeResponse,
)
def update_farm_infrastructure_type(
    infrastructure_type_id: int,
    infrastructure_type_data: InfrastructureTypeUpdate,
    db: SessionDep,
) -> InfrastructureTypeResponse:
    """Update a farm infrastructure type by ID."""
    infrastructure_type = get_or_404(
        db,
        InfrastructureType,
        infrastructure_type_id,
        "Farm infrastructure type",
    )

    return infrastructure_type_service.update_farm_infrastructure_type(
        db,
        infrastructure_type,
        infrastructure_type_data,
    )


@router.delete(
    "/{infrastructure_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_farm_infrastructure_type(
    infrastructure_type_id: int,
    db: SessionDep,
) -> None:
    """Delete a farm infrastructure type by ID."""
    infrastructure_type = get_or_404(
        db,
        InfrastructureType,
        infrastructure_type_id,
        "Farm infrastructure type",
    )

    infrastructure_type_service.delete_farm_infrastructure_type(
        db,
        infrastructure_type,
    )
