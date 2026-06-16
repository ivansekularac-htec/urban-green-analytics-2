from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.farms import farm as farm_crud
from app.database import get_db
from app.schemas.farms.farm import FarmCreate, FarmResponse, FarmUpdate

router = APIRouter(prefix="/farm", tags=["Farm"])

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


@router.put(
    "/{farm_id}",
    response_model=FarmResponse,
)
def update_farm(
    farm_id: int,
    payload: FarmUpdate,
    db: DBSession,
) -> FarmResponse:
    """Update an existing farm."""

    farm = farm_crud.get(
        db=db,
        farm_id=farm_id,
    )

    if farm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found",
        )

    return farm_crud.update(
        db=db,
        farm=farm,
        payload=payload,
    )


@router.delete(
    "/{farm_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_farm(
    farm_id: int,
    db: DBSession,
) -> None:
    """Delete a farm."""

    farm = farm_crud.get(
        db=db,
        farm_id=farm_id,
    )

    if farm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farm not found",
        )

    farm_crud.delete(
        db=db,
        farm=farm,
    )
