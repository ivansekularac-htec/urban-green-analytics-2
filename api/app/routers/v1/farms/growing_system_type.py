from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import GrowingSystemType
from app.schemas import GrowingSystemTypeCreate, GrowingSystemTypeResponse

growing_system_type_router = APIRouter(
    prefix="/growing-system-types",
    tags=["Growing System Types"],
)


@growing_system_type_router.get(
    "/",
    response_model=list[GrowingSystemTypeResponse],
)
def get_growing_system_types(
    db: Session = Depends(get_db),
):
    return db.query(GrowingSystemType).all()


@growing_system_type_router.post(
    "/",
    response_model=GrowingSystemTypeResponse,
    status_code=201,
)
def create_growing_system_type(
    growing_system_type_data: GrowingSystemTypeCreate,
    db: Session = Depends(get_db),
):
    growing_system_type = GrowingSystemType(
        **growing_system_type_data.model_dump(),
    )

    db.add(growing_system_type)
    db.commit()
    db.refresh(growing_system_type)

    return growing_system_type
