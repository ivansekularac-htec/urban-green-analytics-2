from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CropCategory
from app.schemas import CropCategoryCreate, CropCategoryResponse, CropCategoryUpdate

crop_category_router = APIRouter(
    prefix="/crop-categories",
    tags=["Crop Categories"],
)


@crop_category_router.get(
    "/",
    response_model=list[CropCategoryResponse],
)
def get_crop_categories(
    db: Session = Depends(get_db),
):
    return db.query(CropCategory).all()


@crop_category_router.post(
    "/",
    response_model=CropCategoryResponse,
    status_code=201,
)
def create_crop_category(
    crop_category_data: CropCategoryCreate,
    db: Session = Depends(get_db),
):
    crop_category = CropCategory(
        **crop_category_data.model_dump(),
    )

    db.add(crop_category)
    db.commit()
    db.refresh(crop_category)

    return crop_category


@crop_category_router.put(
    "/{category_id}",
    response_model=CropCategoryResponse,
)
def update_crop_category(
    category_id: int,
    category_data: CropCategoryUpdate,
    db: Session = Depends(get_db),
):
    category = db.query(CropCategory).filter(CropCategory.id == category_id).first()

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Crop category not found",
        )

    for field, value in category_data.model_dump(
        exclude_unset=True,
    ).items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)

    return category
