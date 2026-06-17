from fastapi import APIRouter, HTTPException, status

from app.crud.farms import farm as farm_crud
from app.routers.helpers import DBSession, PaginationDep
from app.schemas.farms.farm import FarmCreate, FarmResponse, FarmUpdate

router = APIRouter(prefix="/farm", tags=["Farm"])


@router.post(
    "/",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_farm(
    payload: FarmCreate,
    db: DBSession,
) -> FarmResponse:
    """
    Create a new farm.

    Args:
        payload: Farm data to create.
        db: Active database session.

    Returns:
        The newly created farm.
    """
    return farm_crud.create(db, payload)


@router.get(
    "/{farm_id}",
    response_model=FarmResponse,
)
def get_farm(
    farm_id: int,
    db: DBSession,
) -> FarmResponse:
    """
    Retrieve a farm by its ID.

    Args:
        farm_id: Unique identifier of the farm.
        db: Active database session.

    Returns:
        The requested farm.

    Raises:
        HTTPException: If the farm does not exist.
    """
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
    pagination: PaginationDep,
) -> list[FarmResponse]:
    """
    Retrieve all farms.

    Args:
        db: Active database session.

    Returns:
        A list of all farms.
    """
    return farm_crud.get_all(
        db=db,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.put(
    "/{farm_id}",
    response_model=FarmResponse,
)
def update_farm(
    farm_id: int,
    payload: FarmUpdate,
    db: DBSession,
) -> FarmResponse:
    """
    Update an existing farm.

    Args:
        farm_id: Unique identifier of the farm.
        payload: Updated farm data.
        db: Active database session.

    Returns:
        The updated farm.

    Raises:
        HTTPException: If the farm does not exist.
    """
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
    """
    Delete a farm.

    Args:
        farm_id: Unique identifier of the farm.
        db: Active database session.

    Raises:
        HTTPException: If the farm does not exist.
    """
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
