from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Harvest
from app.schemas import HarvestCreate, HarvestResponse, HarvestUpdate

harvest_router = APIRouter(
    prefix="/harvests",
    tags=["Harvests"],
)


@harvest_router.get(
    "/",
    response_model=list[HarvestResponse],
)
def get_harvests(
    db: Session = Depends(get_db),
):
    return db.query(Harvest).all()


@harvest_router.post(
    "/",
    response_model=HarvestResponse,
    status_code=201,
)
def create_harvest(
    harvest_data: HarvestCreate,
    db: Session = Depends(get_db),
):
    harvest = Harvest(
        **harvest_data.model_dump(),
    )

    db.add(harvest)
    db.commit()
    db.refresh(harvest)

    return harvest


@harvest_router.put(
    "/{harvest_id}",
    response_model=HarvestResponse,
)
def update_harvest(
    harvest_id: int,
    harvest_data: HarvestUpdate,
    db: Session = Depends(get_db),
):
    harvest = db.query(Harvest).filter(Harvest.id == harvest_id).first()

    if harvest is None:
        raise HTTPException(
            status_code=404,
            detail="Harvest not found",
        )

    for field, value in harvest_data.model_dump(
        exclude_unset=True,
    ).items():
        setattr(harvest, field, value)

    db.commit()
    db.refresh(harvest)

    return harvest
