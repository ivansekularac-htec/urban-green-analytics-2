from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.database import DbSession
from app.models.farms.infrastructure_type import InfrastructureType
from app.schemas.farms.infrastructure_type import (
    InfrastructureTypeCreate,
    InfrastructureTypeResponse,
    InfrastructureTypeUpdate,
)

infrastructure_types_router = APIRouter(
    prefix="/infrastructure-types", tags=["infrastructure-types"]
)


@infrastructure_types_router.post(
    "/",
    response_model=InfrastructureTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_infrastructure_type(
    payload: InfrastructureTypeCreate,
    db: DbSession,
) -> InfrastructureType:
    infrastructure_type = InfrastructureType(**payload.model_dump())

    db.add(infrastructure_type)
    db.commit()
    db.refresh(infrastructure_type)

    return infrastructure_type


@infrastructure_types_router.get(
    "/",
    response_model=list[InfrastructureTypeResponse],
)
def get_infrastructure_types(
    db: DbSession,
) -> list[InfrastructureType]:
    return db.scalars(select(InfrastructureType)).all()


@infrastructure_types_router.get(
    "/{infrastructure_type_id}",
    response_model=InfrastructureTypeResponse,
)
def get_infrastructure_type(
    infrastructure_type_id: int,
    db: DbSession,
) -> InfrastructureType:
    infrastructure_type = db.scalar(
        select(InfrastructureType).where(InfrastructureType.id == infrastructure_type_id)
    )

    if infrastructure_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Infrastructure type not found",
        )

    return infrastructure_type


@infrastructure_types_router.put(
    "/{infrastructure_type_id}",
    response_model=InfrastructureTypeResponse,
)
def update_infrastructure_type(
    infrastructure_type_id: int,
    payload: InfrastructureTypeUpdate,
    db: DbSession,
) -> InfrastructureType:
    infrastructure_type = db.scalar(
        select(InfrastructureType).where(InfrastructureType.id == infrastructure_type_id)
    )

    if infrastructure_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Infrastructure type not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(infrastructure_type, field, value)

    db.commit()

    return infrastructure_type


@infrastructure_types_router.delete(
    "/{infrastructure_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_infrastructure_type(
    infrastructure_type_id: int,
    db: DbSession,
) -> None:
    infrastructure_type = db.scalar(
        select(InfrastructureType).where(InfrastructureType.id == infrastructure_type_id)
    )

    if infrastructure_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Infrastructure type not found",
        )

    db.delete(infrastructure_type)
    db.commit()
