from fastapi import APIRouter, status

from app.database import DbSession
from app.schemas.crops.crop_category import (
    CropCategoryCreate,
    CropCategoryResponse,
    CropCategoryUpdate,
)
from app.services.crops.crop_category import CropCategoryService

crop_category_router = APIRouter(
    prefix="/crop-categories",
    tags=["Crop Categories"],
)

service = CropCategoryService()


@crop_category_router.post(
    "", response_model=CropCategoryResponse, status_code=status.HTTP_201_CREATED
)
def create_crop_category(
    payload: CropCategoryCreate,
    db: DbSession,
):
    return service.create(db, payload)


@crop_category_router.get("", response_model=list[CropCategoryResponse])
def get_crop_categories(
    db: DbSession,
):
    return service.get_all(db)


@crop_category_router.get("/{category_id}", response_model=CropCategoryResponse)
def get_crop_category(
    category_id: int,
    db: DbSession,
):
    return service.get(db, category_id)


@crop_category_router.put("/{category_id}", response_model=CropCategoryResponse)
def update_crop_category(
    category_id: int,
    payload: CropCategoryUpdate,
    db: DbSession,
):
    """
    Update crop category by ID.
    """
    return service.update(db, category_id, payload)


@crop_category_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crop_category(
    category_id: int,
    db: DbSession,
):
    service.delete(db, category_id)
    return None
