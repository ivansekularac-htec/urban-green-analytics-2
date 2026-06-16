from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.database import DbSession
from app.models.farms.farm import Farm
from app.schemas.farms.farm import (
    FarmCreate,
    FarmResponse,
    FarmUpdate,
)

farms_router = APIRouter(prefix="/farms", tags=["farms"])


@farms_router.post(
    "/",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_farm(
    payload: FarmCreate,
    db: DbSession,
) -> Farm:
    farm = Farm(**payload.model_dump())

    db.add(farm)
    db.commit()
    db.refresh(farm)

    return farm


@farms_router.get(
    "/",
    response_model=list[FarmResponse],
)
def get_farms(
    db: DbSession,
) -> list[Farm]:
    return db.scalars(select(Farm)).all()


@farms_router.get(
    "/{farm_id}",
    response_model=FarmResponse,
)
def get_farm(
    farm_id: int,
    db: DbSession,
) -> Farm:
    farm = db.scalar(select(Farm).where(Farm.id == farm_id))

    if farm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found",
        )

    return farm


@farms_router.put(
    "/{farm_id}",
    response_model=FarmResponse,
)
def update_farm(
    farm_id: int,
    payload: FarmUpdate,
    db: DbSession,
) -> Farm:
    farm = db.scalar(select(Farm).where(Farm.id == farm_id))

    if farm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(farm, field, value)

    db.commit()

    return farm


@farms_router.delete(
    "/{farm_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_farm(
    farm_id: int,
    db: DbSession,
) -> None:
    farm = db.scalar(select(Farm).where(Farm.id == farm_id))

    if farm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found",
        )

    db.delete(farm)
    db.commit()
