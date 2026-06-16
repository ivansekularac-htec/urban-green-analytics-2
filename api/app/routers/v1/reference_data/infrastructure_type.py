from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.farms.infrastructure_type import (
    InfrastructureTypeCreate,
    InfrastructureTypeResponse,
    InfrastructureTypeUpdate,
)
from app.services.reference_data import infrastructure_type as infrastructure_type_service

router = APIRouter(prefix="/infrastructure-types", tags=["infrastructure-types"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[InfrastructureTypeResponse])
def get_infrastructure_types(db: DbSession):
    """List all infrastructure types."""
    return infrastructure_type_service.get_infrastructure_types(db)


@router.get("/{infrastructure_type_id}", response_model=InfrastructureTypeResponse)
def get_infrastructure_type(infrastructure_type_id: int, db: DbSession):
    """Retrieve a single infrastructure type by ID."""
    infrastructure_type = infrastructure_type_service.get_infrastructure_type(
        db, infrastructure_type_id
    )
    if not infrastructure_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Infrastructure type not found"
        )
    return infrastructure_type


@router.post("/", response_model=InfrastructureTypeResponse, status_code=status.HTTP_201_CREATED)
def create_infrastructure_type(payload: InfrastructureTypeCreate, db: DbSession):
    """Create a new infrastructure type."""
    return infrastructure_type_service.create_infrastructure_type(db, payload)


@router.put("/{infrastructure_type_id}", response_model=InfrastructureTypeResponse)
def update_infrastructure_type(
    infrastructure_type_id: int, payload: InfrastructureTypeUpdate, db: DbSession
):
    infrastructure_type = infrastructure_type_service.get_infrastructure_type(
        db, infrastructure_type_id
    )
    if not infrastructure_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Infrastructure type not found"
        )
    return infrastructure_type_service.update_infrastructure_type(db, infrastructure_type, payload)


@router.delete("/{infrastructure_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_infrastructure_type(infrastructure_type_id: int, db: DbSession):
    """Delete a infrastructure type."""
    infrastructure_type = infrastructure_type_service.get_infrastructure_type(
        db, infrastructure_type_id
    )
    if not infrastructure_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Infrastructure type not found"
        )
    infrastructure_type_service.delete_infrastructure_type(db, infrastructure_type)
