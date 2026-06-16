from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Farm
from app.schemas import FarmCreate, FarmResponse, FarmUpdate

farm_router = APIRouter(
    prefix="/farms",
    tags=["Farms"],
)


@farm_router.get(
    "/",
    response_model=list[FarmResponse],
)
def get_farms(
    db: Session = Depends(get_db),
):
    return db.query(Farm).all()


@farm_router.post(
    "/",
    response_model=FarmResponse,
    status_code=201,
)
def create_farm(
    farm_data: FarmCreate,
    db: Session = Depends(get_db),
):
    farm = Farm(
        **farm_data.model_dump(),
    )

    db.add(farm)
    db.commit()
    db.refresh(farm)

    return farm


@farm_router.put(
    "/{farm_id}",
    response_model=FarmResponse,
)
def update_farm(
    farm_id: int,
    farm_data: FarmUpdate,
    db: Session = Depends(get_db),
):
    farm = db.query(Farm).filter(Farm.id == farm_id).first()

    if farm is None:
        raise HTTPException(
            status_code=404,
            detail="Farm not found",
        )

    for field, value in farm_data.model_dump(
        exclude_unset=True,
    ).items():
        setattr(farm, field, value)

    db.commit()
    db.refresh(farm)

    return farm
