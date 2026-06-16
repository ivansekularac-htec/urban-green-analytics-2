from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.farms import growing_system_type as growing_system_type_crud
from app.database import get_db
from app.schemas.farms.growing_system_type import GrowingSystemTypeCreate, GrowingSystemTypeResponse

router = APIRouter(prefix="/growing_system_type", tags=["Growing System Type"])

DBSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/",
    response_model=GrowingSystemTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_growing_system_type(
    payload: GrowingSystemTypeCreate,
    db: DBSession,
) -> GrowingSystemTypeResponse:
    """
    Create a new growing system type.

    Args:
        payload: Growing system type data to create.
        db: Active database session.

    Returns:
        The newly created growing system type.
    """
    return growing_system_type_crud.create(db, payload)


@router.get(
    "/{growing_system_type_id}",
    response_model=GrowingSystemTypeResponse,
)
def get_growing_system_type(
    growing_system_type_id: int,
    db: DBSession,
) -> GrowingSystemTypeResponse:
    """
    Retrieve a growing system type by its ID.

    Args:
        growing_system_type_id: Unique identifier of the growing system type.
        db: Active database session.

    Returns:
        The requested growing system type.

    Raises:
        HTTPException: If the growing system type does not exist.
    """
    growing_system_type = growing_system_type_crud.get(db, growing_system_type_id)

    if growing_system_type is None:
        raise HTTPException(
            status_code=404,
            detail="Growing System Type not found",
        )

    return growing_system_type


@router.get(
    "/",
    response_model=list[GrowingSystemTypeResponse],
)
def get_growing_system_types(
    db: DBSession,
) -> list[GrowingSystemTypeResponse]:
    """
    Retrieve all growing system types.

    Args:
        db: Active database session.

    Returns:
        A list of all growing system types.
    """
    return growing_system_type_crud.get_all(db)
