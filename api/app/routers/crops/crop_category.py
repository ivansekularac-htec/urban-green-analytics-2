from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.crops import crop_category as crop_category_crud
from app.database import get_db
from app.schemas.crops.crop_category import CropCategoryCreate, CropCategoryResponse

router = APIRouter(prefix="/crop_category", tags=["Crop Category"])

DBSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/",
    response_model=CropCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_crop_category(
    payload: CropCategoryCreate,
    db: DBSession,
) -> CropCategoryResponse:
    return crop_category_crud.create(db, payload)


@router.get(
    "/{crop_category_id}",
    response_model=CropCategoryResponse,
)
def get_crop_category(
    crop_id: int,
    db: DBSession,
) -> CropCategoryResponse:
    crop_category = crop_category_crud.get(db, crop_id)

    if crop_category is None:
        raise HTTPException(
            status_code=404,
            detail="Crop Category not found",
        )

    return crop_category


@router.get(
    "/",
    response_model=list[CropCategoryResponse],
)
def get_crop_categories(
    db: DBSession,
) -> list[CropCategoryResponse]:
    return crop_category_crud.get_all(db)
