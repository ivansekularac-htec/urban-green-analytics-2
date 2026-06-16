from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.farms import infrasctructure_type as infrasctructure_type_crud
from app.database import get_db
from app.schemas.farms.infrastructure_type import (
    InfrastructureTypeCreate,
    InfrastructureTypeResponse,
)

router = APIRouter(prefix="/infrasctructure_type", tags=["Infrasctructure Type"])

DBSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/",
    response_model=InfrastructureTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_infrasctructure_type(
    payload: InfrastructureTypeCreate,
    db: DBSession,
) -> InfrastructureTypeResponse:
    return infrasctructure_type_crud.create(db, payload)


@router.get(
    "/{infrasctructure_type_id}",
    response_model=InfrastructureTypeResponse,
)
def get_infrasctructure_type(
    infrasctructure_type_id: int,
    db: DBSession,
) -> InfrastructureTypeResponse:
    infrasctructure_type = infrasctructure_type_crud.get(db, infrasctructure_type_id)

    if infrasctructure_type is None:
        raise HTTPException(
            status_code=404,
            detail="Infrasctructure Type not found",
        )

    return infrasctructure_type


@router.get(
    "/",
    response_model=list[InfrastructureTypeResponse],
)
def get_infrasctructure_types(
    db: DBSession,
) -> list[InfrastructureTypeResponse]:
    return infrasctructure_type_crud.get_all(db)
