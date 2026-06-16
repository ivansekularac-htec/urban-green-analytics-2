from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.farms import farm as farm_crud
from app.database import get_db
from app.schemas.farms.farm import FarmCreate, FarmResponse

router = APIRouter(prefix="/v1/farm", tags=["Farm"])

DBSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_farm(
    payload: FarmCreate,
    db: DBSession,
) -> FarmResponse:
    return farm_crud.create(db, payload)


@router.get(
    "/{farm_id}",
    response_model=FarmResponse,
)
def get_farm(
    farm_id: int,
    db: DBSession,
) -> FarmResponse:
    farm = farm_crud.get(db, farm_id)

    if farm is None:
        raise HTTPException(
            status_code=404,
            detail="Farm not found",
        )

    return farm


@router.get(
    "/",
    response_model=list[FarmResponse],
)
def get_farms(
    db: DBSession,
) -> list[FarmResponse]:
    return farm_crud.get_all(db)
