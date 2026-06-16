from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.database import DbSession
from app.models.harvests.harvest import Harvest
from app.schemas.crops import crop
from app.schemas.harvests.harvest import (
    HarvestCreate,
    HarvestResponse,
    HarvestUpdate,
)

harvests_router = APIRouter(prefix="/harvests", tags=["harvests"])


@harvests_router.post(
    "/",
    response_model=HarvestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_harvest(
    payload: HarvestCreate,
    db: DbSession,
) -> Harvest:
    harvest = Harvest(**payload.model_dump())

    db.add(harvest)
    db.commit()
    db.refresh(crop)

    return crop


@harvests_router.get(
    "/",
    response_model=list[HarvestResponse],
)
def get_harvests(
    db: DbSession,
) -> list[Harvest]:
    return db.scalars(select(Harvest)).all()


@harvests_router.get(
    "/{harvest_id}",
    response_model=HarvestResponse,
)
def get_harvest(
    harvest_id: int,
    db: DbSession,
) -> Harvest:
    harvest = db.scalar(select(Harvest).where(Harvest.id == harvest_id))

    if harvest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Harvest not found",
        )

    return harvest


@harvests_router.put(
    "/{harvest_id}",
    response_model=HarvestResponse,
)
def update_harvest(
    harvest_id: int,
    payload: HarvestUpdate,
    db: DbSession,
) -> Harvest:
    harvest = db.scalar(select(Harvest).where(Harvest.id == harvest_id))

    if harvest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Harvest not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(harvest, field, value)

    db.commit()

    return harvest


@harvests_router.delete(
    "/{harvest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_harvest(
    harvest_id: int,
    db: DbSession,
) -> None:
    harvest = db.scalar(select(Harvest).where(Harvest.id == harvest_id))

    if harvest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Harvest not found",
        )

    db.delete(harvest)
    db.commit()
