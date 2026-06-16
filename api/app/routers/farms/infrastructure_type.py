from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.farms import infrastructure_type as infrastructure_type_crud
from app.database import get_db
from app.schemas.farms.infrastructure_type import (
    InfrastructureTypeCreate,
    InfrastructureTypeResponse,
)

router = APIRouter(prefix="/infrastructure_type", tags=["infrastructure Type"])

DBSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/",
    response_model=InfrastructureTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_infrastructure_type(
    payload: InfrastructureTypeCreate,
    db: DBSession,
) -> InfrastructureTypeResponse:
    """
    Create a new infrastructure type.

    Args:
        payload: Infrastructure type data to create.
        db: Active database session.

    Returns:
        The newly created infrastructure type.
    """
    return infrastructure_type_crud.create(db, payload)


@router.get(
    "/{infrastructure_type_id}",
    response_model=InfrastructureTypeResponse,
)
def get_infrastructure_type(
    infrastructure_type_id: int,
    db: DBSession,
) -> InfrastructureTypeResponse:
    """
    Retrieve an infrastructure type by its ID.

    Args:
        infrastructure_type_id: Unique identifier of the infrastructure type.
        db: Active database session.

    Returns:
        The requested infrastructure type.

    Raises:
        HTTPException: If the infrastructure type does not exist.
    """
    infrastructure_type = infrastructure_type_crud.get(
        db,
        infrastructure_type_id,
    )

    if infrastructure_type is None:
        raise HTTPException(
            status_code=404,
            detail="infrastructure Type not found",
        )

    return infrastructure_type


@router.get(
    "/",
    response_model=list[InfrastructureTypeResponse],
)
def get_infrastructure_types(
    db: DBSession,
) -> list[InfrastructureTypeResponse]:
    """
    Retrieve all infrastructure types.

    Args:
        db: Active database session.

    Returns:
        A list of all infrastructure types.
    """
    return infrastructure_type_crud.get_all(db)
