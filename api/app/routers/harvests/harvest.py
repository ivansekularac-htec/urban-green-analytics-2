from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.harvests import harvest as harvest_crud
from app.database import get_db
from app.schemas.harvests.harvest import HarvestCreate, HarvestResponse

router = APIRouter(prefix="/harvest", tags=["Harvest"])

DBSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/",
    response_model=HarvestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_harvest(
    payload: HarvestCreate,
    db: DBSession,
) -> HarvestResponse:
    return harvest_crud.create(db, payload)


@router.get(
    "/{harvest_id}",
    response_model=HarvestResponse,
)
def get_harvest(
    harvest_id: int,
    db: DBSession,
) -> HarvestResponse:
    harvest = harvest_crud.get(db, harvest_id)

    if harvest is None:
        raise HTTPException(
            status_code=404,
            detail="Harvest not found",
        )

    return harvest


@router.get(
    "/",
    response_model=list[HarvestResponse],
)
def get_harvests(
    db: DBSession,
) -> list[HarvestResponse]:
    return harvest_crud.get_all(db)
