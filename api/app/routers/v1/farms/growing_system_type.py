"""
growing_system_types.py
API routes for growing system type management.

This module defines CRUD endpoints for GrowingSystemType resources.
"""

from fastapi import APIRouter, status

from app.database import SessionDep
from app.models.farms.growing_system_type import GrowingSystemType
from app.schemas.farms.growing_system_type import (
    GrowingSystemTypeCreate,
    GrowingSystemTypeResponse,
    GrowingSystemTypeUpdate,
)
from app.services.common import get_or_404
from app.services.farms import growing_system_type_service

router = APIRouter(
    prefix="/growing-system-types",
    tags=["Growing System Types"],
)


@router.post(
    "",
    response_model=GrowingSystemTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_growing_system_type(
    growing_system_type_data: GrowingSystemTypeCreate,
    db: SessionDep,
) -> GrowingSystemTypeResponse:
    """Create a new growing system type."""
    return growing_system_type_service.create_growing_system_type(
        db,
        growing_system_type_data,
    )


@router.get(
    "",
    response_model=list[GrowingSystemTypeResponse],
)
def get_growing_system_types(
    db: SessionDep,
) -> list[GrowingSystemTypeResponse]:
    """Return all growing system types."""
    return growing_system_type_service.get_growing_system_types(db)


@router.get(
    "/{growing_system_type_id}",
    response_model=GrowingSystemTypeResponse,
)
def get_growing_system_type(
    growing_system_type_id: int,
    db: SessionDep,
) -> GrowingSystemTypeResponse:
    """Return a growing system type by ID."""
    return get_or_404(
        db,
        GrowingSystemType,
        growing_system_type_id,
        "Growing system type",
    )


@router.put(
    "/{growing_system_type_id}",
    response_model=GrowingSystemTypeResponse,
)
def update_growing_system_type(
    growing_system_type_id: int,
    growing_system_type_data: GrowingSystemTypeUpdate,
    db: SessionDep,
) -> GrowingSystemTypeResponse:
    """Update a growing system type by ID."""
    growing_system_type = get_or_404(
        db,
        GrowingSystemType,
        growing_system_type_id,
        "Growing system type",
    )

    return growing_system_type_service.update_growing_system_type(
        db,
        growing_system_type,
        growing_system_type_data,
    )


@router.delete(
    "/{growing_system_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_growing_system_type(
    growing_system_type_id: int,
    db: SessionDep,
) -> None:
    """Delete a growing system type by ID."""
    growing_system_type = get_or_404(
        db,
        GrowingSystemType,
        growing_system_type_id,
        "Growing system type",
    )

    growing_system_type_service.delete_growing_system_type(
        db,
        growing_system_type,
    )
