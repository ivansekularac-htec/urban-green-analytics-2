from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.crops import crop as crop_crud
from app.database import get_db
from app.schemas.crops.crop import CropCreate, CropResponse

router = APIRouter(prefix="/crop", tags=["Crop"])

DBSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/",
    response_model=CropResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_crop(
    payload: CropCreate,
    db: DBSession,
) -> CropResponse:
    """
    Create a new crop.

    Args:
        payload: Crop data to create.
        db: Active database session.

    Returns:
        The newly created crop.
    """
    return crop_crud.create(db, payload)


@router.get(
    "/{crop_id}",
    response_model=CropResponse,
)
def get_crop(
    crop_id: int,
    db: DBSession,
) -> CropResponse:
    """
    Retrieve a crop by its ID.

    Args:
        crop_id: Unique identifier of the crop.
        db: Active database session.

    Returns:
        The requested crop.

    Raises:
        HTTPException: If the crop does not exist.
    """
    crop = crop_crud.get(db, crop_id)

    if crop is None:
        raise HTTPException(
            status_code=404,
            detail="Crop not found",
        )

    return crop


@router.get(
    "/",
    response_model=list[CropResponse],
)
def get_crops(
    db: DBSession,
) -> list[CropResponse]:
    """
    Retrieve all crops.

    Args:
        db: Active database session.

    Returns:
        A list of all crops.
    """
    return crop_crud.get_all(db)
