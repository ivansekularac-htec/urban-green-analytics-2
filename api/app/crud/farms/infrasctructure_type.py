from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.farms.infrastructure_type import InfrastructureType
from app.schemas.farms.infrastructure_type import InfrastructureTypeCreate


def create(
    db: Session,
    payload: InfrastructureTypeCreate,
) -> InfrastructureType:

    obj = InfrastructureType(**payload.model_dump())

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


def get(
    db: Session,
    infrastructure_type_id: int,
) -> InfrastructureType | None:

    return db.get(InfrastructureType, infrastructure_type_id)


def get_all(
    db: Session,
) -> list[InfrastructureType]:

    return list(db.scalars(select(InfrastructureType)).all())
