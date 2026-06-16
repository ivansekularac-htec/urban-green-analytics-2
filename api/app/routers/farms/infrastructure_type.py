from fastapi import APIRouter, status

from app.database import DbSession
from app.schemas.farms.infrastructure_type import (
    InfrastructureTypeCreate,
    InfrastructureTypeResponse,
    InfrastructureTypeUpdate,
)
from app.services.farms.infrastructure_type import InfrastructureTypeService

infrastructure_type_router = APIRouter(
    prefix="/infrastructure-types",
    tags=["Infrastructure Types"],
)

service = InfrastructureTypeService()


@infrastructure_type_router.post(
    "", response_model=InfrastructureTypeResponse, status_code=status.HTTP_201_CREATED
)
def create_infrastructure_type(
    payload: InfrastructureTypeCreate,
    db: DbSession,
):
    """
    Create a new InfrastructureType.

    Args:
        payload (InfrastructureTypeCreate): Request body.
        db (Session): Database session.

    Returns:
        InfrastructureTypeResponse: Created entity.
    """
    return service.create(db, payload)


@infrastructure_type_router.get("", response_model=list[InfrastructureTypeResponse])
def get_all_infrastructure_types(
    db: DbSession,
):
    """
    Retrieve all InfrastructureType records.

    Returns:
        list[InfrastructureTypeResponse]: List of entities.
    """
    return service.get_all(db)


@infrastructure_type_router.get("/{type_id}", response_model=InfrastructureTypeResponse)
def get_infrastructure_type(
    type_id: int,
    db: DbSession,
):
    """
    Retrieve InfrastructureType by ID.

    Args:
        type_id (int): Entity ID.
        db (Session): Database session.

    Returns:
        InfrastructureTypeResponse: Requested entity.
    """
    return service.get(db, type_id)


@infrastructure_type_router.put("/{type_id}", response_model=InfrastructureTypeResponse)
def update_infrastructure_type(
    type_id: int,
    payload: InfrastructureTypeUpdate,
    db: DbSession,
):
    """
    Update InfrastructureType (partial update).

    Args:
        type_id (int): Entity ID.
        payload (InfrastructureTypeUpdate): Update data.
        db (Session): Database session.

    Returns:
        InfrastructureTypeResponse: Updated entity.
    """
    return service.update(db, type_id, payload)


@infrastructure_type_router.delete("/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_infrastructure_type(
    type_id: int,
    db: DbSession,
):
    """
    Delete InfrastructureType.

    Args:
        type_id (int): Entity ID.
        db (Session): Database session.

    Returns:
        None
    """
    return service.delete(db, type_id)
