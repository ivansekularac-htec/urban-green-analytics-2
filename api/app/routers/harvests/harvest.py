from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.harvests import harvest as harvest_crud
from app.database import get_db
from app.schemas.harvests.harvest import HarvestCreate, HarvestResponse, HarvestUpdate

router = APIRouter(prefix="/harvest", tags=["Harvest"])

DBSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/",
    response_model=HarvestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_harvest(
    payload: HarvestCreate,
    db: DBSession,
) -> HarvestResponse:
    """
    Create a new harvest.

    Args:
        payload: Harvest data to create.
        db: Active database session.

    Returns:
        The newly created harvest.
    """
    return harvest_crud.create(db, payload)


@router.get(
    "/{harvest_id}",
    response_model=HarvestResponse,
)
def get_harvest(
    harvest_id: int,
    db: DBSession,
) -> HarvestResponse:
    """
    Retrieve a harvest by its ID.

    Args:
        harvest_id: Unique identifier of the harvest.
        db: Active database session.

    Returns:
        The requested harvest.

    Raises:
        HTTPException: If the harvest does not exist.
    """
    harvest = harvest_crud.get(db, harvest_id)

    if harvest is None:
        raise HTTPException(
            status_code=404,
            detail="Harvest not found",
        )

    return harvest


@router.get(
    "/",
    response_model=list[HarvestResponse],
)
def get_harvests(
    db: DBSession,
) -> list[HarvestResponse]:
    """
    Retrieve all harvests.

    Args:
        db: Active database session.

    Returns:
        A list of all harvests.
    """
    return harvest_crud.get_all(db)


@router.put(
    "/{harvest_id}",
    response_model=HarvestResponse,
)
def update_harvest(
    harvest_id: int,
    payload: HarvestUpdate,
    db: DBSession,
) -> HarvestResponse:
    """
    Update an existing harvest.

    Args:
        harvest_id: Unique identifier of the harvest.
        payload: Updated harvest data.
        db: Active database session.

    Returns:
        The updated harvest.

    Raises:
        HTTPException: If the harvest does not exist.
    """
    harvest = harvest_crud.get(
        db=db,
        harvest_id=harvest_id,
    )

    if harvest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Harvest not found",
        )

    return harvest_crud.update(
        db=db,
        harvest=harvest,
        payload=payload,
    )


@router.delete(
    "/{harvest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_harvest(
    harvest_id: int,
    db: DBSession,
) -> None:
    """
    Delete a harvest.

    Args:
        harvest_id: Unique identifier of the harvest.
        db: Active database session.

    Raises:
        HTTPException: If the harvest does not exist.
    """
    harvest = harvest_crud.get(
        db=db,
        harvest_id=harvest_id,
    )

    if harvest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Harvest not found",
        )

    harvest_crud.delete(
        db=db,
        harvest=harvest,
    )
