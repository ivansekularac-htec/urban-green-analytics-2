"""
Router for Farm entity.

Exposes REST API endpoints for:
- creating farms
- retrieving farms
- updating farms
- deleting farms
"""

from fastapi import APIRouter, status

from app.database import DbSession
from app.schemas.farms.farm import FarmCreate, FarmResponse, FarmUpdate
from app.services.farms.farm import FarmService

farm_router = APIRouter(
    prefix="/farms",
    tags=["Farms"],
)

service = FarmService()


@farm_router.post("", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
def create_farm(
    payload: FarmCreate,
    db: DbSession,
):
    """
    Create a new farm.

    Validates:
    - infrastructure_type_id exists
    - growing_system_type_id exists
    """
    return service.create(db, payload)


@farm_router.get("", response_model=list[FarmResponse])
def get_farms(
    db: DbSession,
):
    """
    Retrieve all farms.
    """
    return service.get_all(db)


@farm_router.get("/{farm_id}", response_model=FarmResponse)
def get_farm(
    farm_id: int,
    db: DbSession,
):
    """
    Retrieve a single farm by ID.
    """
    return service.get(db, farm_id)


@farm_router.put("/{farm_id}", response_model=FarmResponse)
def update_farm(
    farm_id: int,
    payload: FarmUpdate,
    db: DbSession,
):
    """
    Update an existing farm.

    Supports partial updates.
    Validates related foreign keys if provided.
    """
    return service.update(db, farm_id, payload)


@farm_router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm(
    farm_id: int,
    db: DbSession,
):
    """
    Delete a farm by ID.
    """
    service.delete(db, farm_id)
    return None
