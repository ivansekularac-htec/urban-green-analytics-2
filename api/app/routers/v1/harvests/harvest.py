from typing import Annotated

from app.services.harvests import harvest as harvest_service
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.harvests.harvest import HarvestCreate, HarvestResponse, HarvestUpdate

router = APIRouter(prefix="/harvests", tags=["harvests"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[HarvestResponse])
def get_harvests(db: DbSession):
    """List all harvests."""
    return harvest_service.get_harvests(db)


@router.get("/{harvest_id}", response_model=HarvestResponse)
def get_harvest(harvest_id: int, db: DbSession):
    """Retrieve a single harvest by ID."""
    harvest = harvest_service.get_harvest(db, harvest_id)
    if not harvest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Harvest not found")
    return harvest


@router.post("/", response_model=HarvestResponse, status_code=status.HTTP_201_CREATED)
def create_harvest(payload: HarvestCreate, db: DbSession):
    """Create a new harvest."""
    return harvest_service.create_harvest(db, payload)


@router.put("/{harvest_id}", response_model=HarvestResponse)
def update_harvest(harvest_id: int, payload: HarvestUpdate, db: DbSession):
    """Update an existing harvest."""
    harvest = harvest_service.get_harvest(db, harvest_id)
    if not harvest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Harvest not found")
    return harvest_service.update_harvest(db, harvest, payload)


@router.delete("/{harvest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_harvest(harvest_id: int, db: DbSession):
    """Delete a harvest."""
    harvest = harvest_service.get_harvest(db, harvest_id)
    if not harvest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Harvest not found")
    harvest_service.delete_harvest(db, harvest)
