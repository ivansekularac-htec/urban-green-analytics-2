from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import InfrastructureType
from app.schemas import InfrastructureTypeCreate, InfrastructureTypeResponse

infrastructure_type_router = APIRouter(
    prefix="/infrastructure-types",
    tags=["Infrastructure Types"],
)


@infrastructure_type_router.get(
    "/",
    response_model=list[InfrastructureTypeResponse],
)
def get_infrastructure_types(
    db: Session = Depends(get_db),
):
    return db.query(InfrastructureType).all()


@infrastructure_type_router.post(
    "/",
    response_model=InfrastructureTypeResponse,
    status_code=201,
)
def create_infrastructure_type(
    infrastructure_type_data: InfrastructureTypeCreate,
    db: Session = Depends(get_db),
):
    infrastructure_type = InfrastructureType(
        **infrastructure_type_data.model_dump(),
    )

    db.add(infrastructure_type)
    db.commit()
    db.refresh(infrastructure_type)

    return infrastructure_type
