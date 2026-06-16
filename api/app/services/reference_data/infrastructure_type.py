from sqlalchemy.orm import Session

from app.models.farms.infrastructure_type import InfrastructureType
from app.schemas.farms.infrastructure_type import InfrastructureTypeCreate, InfrastructureTypeUpdate


def get_infrastructure_types(db: Session) -> list[InfrastructureType]:
    """Query and return all infrastructure types from the database."""
    return db.query(InfrastructureType).all()


def get_infrastructure_type(db: Session, infrastructure_type_id: int) -> InfrastructureType | None:
    """Return a single infrastructure type by ID, or None if not found."""
    return (
        db.query(InfrastructureType).filter(InfrastructureType.id == infrastructure_type_id).first()
    )


def create_infrastructure_type(
    db: Session, payload: InfrastructureTypeCreate
) -> InfrastructureType:
    infrastructure_type = InfrastructureType(**payload.model_dump())
    db.add(infrastructure_type)
    db.commit()
    db.refresh(infrastructure_type)
    return infrastructure_type


def update_infrastructure_type(
    db: Session, infrastructure_type: InfrastructureType, payload: InfrastructureTypeUpdate
) -> InfrastructureType:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(infrastructure_type, field, value)
    db.commit()
    db.refresh(infrastructure_type)
    return infrastructure_type


def delete_infrastructure_type(db: Session, infrastructure_type: InfrastructureType) -> None:
    """Delete a infrastructure type from the database."""
    db.delete(infrastructure_type)
    db.commit()
