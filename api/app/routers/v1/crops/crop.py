from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Crop
from app.schemas import CropCreate, CropResponse, CropUpdate

crop_router = APIRouter(
    prefix="/crops",
    tags=["Crops"],
)


@crop_router.get("/", response_model=list[CropResponse])
def get_crops(db: Session = Depends(get_db)):
    return db.query(Crop).all()


@crop_router.post(
    "/",
    response_model=CropResponse,
    status_code=201,
)
def create_crop(
    crop_data: CropCreate,
    db: Session = Depends(get_db),
):
    crop = Crop(**crop_data.model_dump())

    db.add(crop)
    db.commit()
    db.refresh(crop)

    return crop


@crop_router.put(
    "/{crop_id}",
    response_model=CropResponse,
)
def update_crop(
    crop_id: int,
    crop_data: CropUpdate,
    db: Session = Depends(get_db),
):
    crop = db.query(Crop).filter(Crop.id == crop_id).first()

    if crop is None:
        raise HTTPException(
            status_code=404,
            detail="Crop not found",
        )

    for field, value in crop_data.model_dump(
        exclude_unset=True,
    ).items():
        setattr(crop, field, value)

    db.commit()
    db.refresh(crop)

    return crop


@crop_router.delete(
    "/{crop_id}",
    status_code=204,
)
def delete_crop(
    crop_id: int,
    db: Session = Depends(get_db),
):
    crop = db.query(Crop).filter(Crop.id == crop_id).first()

    if crop is None:
        raise HTTPException(
            status_code=404,
            detail="Crop not found",
        )

    db.delete(crop)
    db.commit()
