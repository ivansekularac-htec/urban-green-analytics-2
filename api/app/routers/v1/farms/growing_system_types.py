from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.database import DbSession
from app.models.farms.growing_system_type import GrowingSystemType
from app.schemas.farms.growing_system_type import (
    GrowingSystemTypeCreate,
    GrowingSystemTypeResponse,
    GrowingSystemTypeUpdate,
)

growing_system_types_router = APIRouter(
    prefix="/growing-system-types", tags=["growing-system-types"]
)


@growing_system_types_router.post(
    "/",
    response_model=GrowingSystemTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_growing_system_type(
    payload: GrowingSystemTypeCreate,
    db: DbSession,
) -> GrowingSystemType:
    growing_system_type = GrowingSystemType(**payload.model_dump())

    db.add(growing_system_type)
    db.commit()
    db.refresh(growing_system_type)

    return growing_system_type


@growing_system_types_router.get(
    "/",
    response_model=list[GrowingSystemTypeResponse],
)
def get_growing_system_types(
    db: DbSession,
) -> list[GrowingSystemType]:
    return db.scalars(select(GrowingSystemType)).all()


@growing_system_types_router.get(
    "/{growing_system_type_id}",
    response_model=GrowingSystemTypeResponse,
)
def get_growing_system_type(
    growing_system_type_id: int,
    db: DbSession,
) -> GrowingSystemType:
    growing_system_type = db.scalar(
        select(GrowingSystemType).where(GrowingSystemType.id == growing_system_type_id)
    )

    if growing_system_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Growing system type not found",
        )

    return growing_system_type


@growing_system_types_router.put(
    "/{growing_system_type_id}",
    response_model=GrowingSystemTypeResponse,
)
def update_growing_system_type(
    growing_system_type_id: int,
    payload: GrowingSystemTypeUpdate,
    db: DbSession,
) -> GrowingSystemType:
    growing_system_type = db.scalar(
        select(GrowingSystemType).where(GrowingSystemType.id == growing_system_type_id)
    )

    if growing_system_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Growing system type not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(growing_system_type, field, value)

    db.commit()

    return growing_system_type


@growing_system_types_router.delete(
    "/{growing_system_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_growing_system_type(
    growing_system_type_id: int,
    db: DbSession,
) -> None:
    growing_system_type = db.scalar(
        select(GrowingSystemType).where(GrowingSystemType.id == growing_system_type_id)
    )

    if growing_system_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Growing system type not found",
        )

    db.delete(growing_system_type)
    db.commit()
