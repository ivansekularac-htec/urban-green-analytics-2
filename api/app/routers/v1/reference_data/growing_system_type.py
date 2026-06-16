from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.farms.growing_system_type import (
    GrowingSystemTypeCreate,
    GrowingSystemTypeResponse,
    GrowingSystemTypeUpdate,
)
from app.services.reference_data import growing_system_type as growing_system_type_service

router = APIRouter(prefix="/growing-system-types", tags=["growing-system-types"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[GrowingSystemTypeResponse])
def get_growing_system_types(db: DbSession):
    """List all growing system types."""
    return growing_system_type_service.get_growing_system_types(db)


@router.get("/{growing_system_type_id}", response_model=GrowingSystemTypeResponse)
def get_growing_system_type(growing_system_type_id: int, db: DbSession):
    """Retrieve a single growing system type by ID."""
    growing_system_type = growing_system_type_service.get_growing_system_type(
        db, growing_system_type_id
    )
    if not growing_system_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Growing system type not found"
        )
    return growing_system_type


@router.post("/", response_model=GrowingSystemTypeResponse, status_code=status.HTTP_201_CREATED)
def create_growing_system_type(payload: GrowingSystemTypeCreate, db: DbSession):
    """Create a new growing system type."""
    return growing_system_type_service.create_growing_system_type(db, payload)


@router.put("/{growing_system_type_id}", response_model=GrowingSystemTypeResponse)
def update_growing_system_type(
    growing_system_type_id: int, payload: GrowingSystemTypeUpdate, db: DbSession
):
    growing_system_type = growing_system_type_service.get_growing_system_type(
        db, growing_system_type_id
    )
    if not growing_system_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Growing system type not found"
        )
    return growing_system_type_service.update_growing_system_type(db, growing_system_type, payload)


@router.delete("/{growing_system_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_growing_system_type(growing_system_type_id: int, db: DbSession):
    """Delete a growing system type."""
    growing_system_type = growing_system_type_service.get_growing_system_type(
        db, growing_system_type_id
    )
    if not growing_system_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Growing system type not found"
        )
    growing_system_type_service.delete_growing_system_type(db, growing_system_type)
