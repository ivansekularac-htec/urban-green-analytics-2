"""
harvests.py
API routes for harvest management.

This module defines CRUD endpoints for Harvest resources.
"""

from fastapi import APIRouter, status

from app.database import SessionDep
from app.models.crops.crop import Crop
from app.models.farms.farm import Farm
from app.models.harvests.harvest import Harvest
from app.models.harvests.quality_grade import QualityGrade
from app.schemas.harvests.harvest import (
    HarvestCreate,
    HarvestResponse,
    HarvestUpdate,
)
from app.services.common import get_or_404
from app.services.harvests import harvest_service

router = APIRouter(
    prefix="/harvests",
    tags=["Harvests"],
)


@router.post(
    "",
    response_model=HarvestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_harvest(
    harvest_data: HarvestCreate,
    db: SessionDep,
) -> HarvestResponse:
    """Create a new harvest."""

    get_or_404(
        db,
        Farm,
        harvest_data.farm_id,
        "Farm",
    )

    get_or_404(
        db,
        Crop,
        harvest_data.crop_id,
        "Crop",
    )

    get_or_404(
        db,
        QualityGrade,
        harvest_data.quality_grade_id,
        "Quality grade",
    )

    return harvest_service.create_harvest(
        db,
        harvest_data,
    )


@router.get(
    "",
    response_model=list[HarvestResponse],
)
def get_harvests(
    db: SessionDep,
) -> list[HarvestResponse]:
    """Return all harvests."""
    return harvest_service.get_harvests(db)


@router.get(
    "/{harvest_id}",
    response_model=HarvestResponse,
)
def get_harvest(
    harvest_id: int,
    db: SessionDep,
) -> HarvestResponse:
    """Return a harvest by ID."""
    return get_or_404(
        db,
        Harvest,
        harvest_id,
        "Harvest",
    )


@router.put(
    "/{harvest_id}",
    response_model=HarvestResponse,
)
def update_harvest(
    harvest_id: int,
    harvest_data: HarvestUpdate,
    db: SessionDep,
) -> HarvestResponse:
    """Update a harvest by ID."""

    harvest = get_or_404(
        db,
        Harvest,
        harvest_id,
        "Harvest",
    )

    if harvest_data.quality_grade_id is not None:
        get_or_404(
            db,
            QualityGrade,
            harvest_data.quality_grade_id,
            "Quality grade",
        )

    return harvest_service.update_harvest(
        db,
        harvest,
        harvest_data,
    )


@router.delete(
    "/{harvest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_harvest(
    harvest_id: int,
    db: SessionDep,
) -> None:
    """Delete a harvest by ID."""

    harvest = get_or_404(
        db,
        Harvest,
        harvest_id,
        "Harvest",
    )

    harvest_service.delete_harvest(
        db,
        harvest,
    )
