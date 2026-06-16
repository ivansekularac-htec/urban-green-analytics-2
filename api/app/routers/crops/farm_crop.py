from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.crops import farm_crop as farm_crop_crud
from app.database import get_db
from app.schemas.crops.farm_crop import FarmCropCreate, FarmCropResponse, FarmCropUpdate

router = APIRouter(prefix="/farm_crop", tags=["FarmCrop"])

DBSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/",
    response_model=FarmCropResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_farm_crop(
    payload: FarmCropCreate,
    db: DBSession,
) -> FarmCropResponse:
    return farm_crop_crud.create(db, payload)


@router.get(
    "/{farm_crop_id}",
    response_model=FarmCropResponse,
)
def get_farm_crop(
    farm_crop_id: int,
    db: DBSession,
) -> FarmCropResponse:
    farm_crop = farm_crop_crud.get(db, farm_crop_id)

    if farm_crop is None:
        raise HTTPException(
            status_code=404,
            detail="Farm Crop not found",
        )

    return farm_crop


@router.get(
    "/",
    response_model=list[FarmCropResponse],
)
def get_farm_crops(
    db: DBSession,
) -> list[FarmCropResponse]:
    return farm_crop_crud.get_all(db)


@router.put(
    "/{farm_crop_id}",
    response_model=FarmCropResponse,
)
def update_farm_crop(
    farm_crop_id: int,
    payload: FarmCropUpdate,
    db: DBSession,
) -> FarmCropResponse:
    """Update an existing farm crop assignment."""

    farm_crop = farm_crop_crud.get(
        db=db,
        farm_crop_id=farm_crop_id,
    )

    if farm_crop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm crop not found",
        )

    return farm_crop_crud.update(
        db=db,
        farm_crop=farm_crop,
        payload=payload,
    )


@router.delete(
    "/{farm_crop_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_farm_crop(
    farm_crop_id: int,
    db: DBSession,
) -> None:
    """Delete a farm crop assignment."""

    farm_crop = farm_crop_crud.get(
        db=db,
        farm_crop_id=farm_crop_id,
    )

    if farm_crop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm crop not found",
        )

    farm_crop_crud.delete(
        db=db,
        farm_crop=farm_crop,
    )
