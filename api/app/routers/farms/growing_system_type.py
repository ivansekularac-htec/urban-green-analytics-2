from fastapi import APIRouter, status

from app.database import DbSession
from app.schemas.farms.growing_system_type import (
    GrowingSystemTypeCreate,
    GrowingSystemTypeResponse,
    GrowingSystemTypeUpdate,
)
from app.services.farms.growing_system_type import GrowingSystemTypeService

growing_system_type_router = APIRouter(
    prefix="/growing-system-types",
    tags=["Growing System Types"],
)

service = GrowingSystemTypeService()


@growing_system_type_router.post(
    "",
    response_model=GrowingSystemTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_type(
    payload: GrowingSystemTypeCreate,
    db: DbSession,
):
    return service.create(db, payload)


@growing_system_type_router.get("", response_model=list[GrowingSystemTypeResponse])
def get_all(db: DbSession):
    return service.get_all(db)


@growing_system_type_router.get("/{type_id}", response_model=GrowingSystemTypeResponse)
def get_by_id(
    type_id: int,
    db: DbSession,
):
    return service.get(db, type_id)


@growing_system_type_router.put("/{type_id}", response_model=GrowingSystemTypeResponse)
def update(
    type_id: int,
    payload: GrowingSystemTypeUpdate,
    db: DbSession,
):
    return service.update(db, type_id, payload)


@growing_system_type_router.delete("/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    type_id: int,
    db: DbSession,
):
    return service.delete(db, type_id)
