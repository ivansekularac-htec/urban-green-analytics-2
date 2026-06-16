from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FarmCrop
from app.schemas import FarmCropCreate, FarmCropResponse, FarmCropUpdate

farm_crop_router = APIRouter(
    prefix="/farm-crops",
    tags=["Farm Crops"],
)


@farm_crop_router.get(
    "/",
    response_model=list[FarmCropResponse],
)
def get_farm_crops(
    db: Session = Depends(get_db),
):
    return db.query(FarmCrop).all()


@farm_crop_router.post(
    "/",
    response_model=FarmCropResponse,
    status_code=201,
)
def create_farm_crop(
    farm_crop_data: FarmCropCreate,
    db: Session = Depends(get_db),
):
    farm_crop = FarmCrop(
        **farm_crop_data.model_dump(),
    )

    db.add(farm_crop)
    db.commit()
    db.refresh(farm_crop)

    return farm_crop


@farm_crop_router.put(
    "/{farm_crop_id}",
    response_model=FarmCropResponse,
)
def update_farm_crop(
    farm_crop_id: int,
    farm_crop_data: FarmCropUpdate,
    db: Session = Depends(get_db),
):
    farm_crop = db.query(FarmCrop).filter(FarmCrop.id == farm_crop_id).first()

    if farm_crop is None:
        raise HTTPException(
            status_code=404,
            detail="Farm crop not found",
        )

    for field, value in farm_crop_data.model_dump(
        exclude_unset=True,
    ).items():
        setattr(farm_crop, field, value)

    db.commit()
    db.refresh(farm_crop)

    return farm_crop
