from fastapi import APIRouter, HTTPException, status

from app.crud.crops import crop_category as crop_category_crud
from app.routers.helpers import DBSession, PaginationDep
from app.schemas.crops.crop_category import CropCategoryCreate, CropCategoryResponse

router = APIRouter(prefix="/crop_category", tags=["Crop Category"])


@router.post(
    "/",
    response_model=CropCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_crop_category(
    payload: CropCategoryCreate,
    db: DBSession,
) -> CropCategoryResponse:
    """
    Create a new crop category.

    Args:
        payload: Crop category data to create.
        db: Active database session.

    Returns:
        The newly created crop category.
    """
    return crop_category_crud.create(db, payload)


@router.get(
    "/{crop_category_id}",
    response_model=CropCategoryResponse,
)
def get_crop_category(
    crop_category_id: int,
    db: DBSession,
) -> CropCategoryResponse:
    """
    Retrieve a crop category by its ID.

    Args:
        crop_id: Unique identifier of the crop category.
        db: Active database session.

    Returns:
        The requested crop category.

    Raises:
        HTTPException: If the crop category does not exist.
    """
    crop_category = crop_category_crud.get(db, crop_category_id)

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
    pagination: PaginationDep,
) -> list[CropCategoryResponse]:
    """
    Retrieve all crop categories.

    Args:
        db: Active database session.

    Returns:
        A list of all crop categories.
    """
    return crop_category_crud.get_all(
        db=db,
        skip=pagination.skip,
        limit=pagination.limit,
    )
