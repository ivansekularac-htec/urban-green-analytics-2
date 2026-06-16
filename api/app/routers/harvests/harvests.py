"""
Router layer for Harvest.

Exposes CRUD endpoints for harvest records.

Delegates all business logic to HarvestService.
"""

from fastapi import APIRouter

from app.database import DbSession
from app.schemas.harvests.harvest import (
    HarvestCreate,
    HarvestResponse,
    HarvestUpdate,
)
from app.services.harvests.harvest import HarvestService

harvest_router = APIRouter(prefix="/harvests", tags=["Harvest"])

service = HarvestService()


@harvest_router.get("", response_model=list[HarvestResponse])
def get_all(
    db: DbSession,
):
    """
    Retrieve all harvest records.
    """
    return service.get_all(db)


@harvest_router.get("/{harvest_id}", response_model=HarvestResponse)
def get_one(
    harvest_id: int,
    db: DbSession,
):
    """
    Retrieve a single Harvest by ID.
    """
    return service.get(db, harvest_id)


@harvest_router.post("", response_model=HarvestResponse)
def create(
    payload: HarvestCreate,
    db: DbSession,
):
    """
    Create a new Harvest record.
    """
    return service.create(db, payload)


@harvest_router.put("/{harvest_id}", response_model=HarvestResponse)
def update(
    harvest_id: int,
    payload: HarvestUpdate,
    db: DbSession,
):
    """
    Update an existing Harvest record (partial update supported).
    """
    return service.update(db, harvest_id, payload)
