from sqlalchemy.orm import Session

from app.models.farms.growing_system_type import GrowingSystemType
from app.schemas.farms.growing_system_type import GrowingSystemTypeCreate, GrowingSystemTypeUpdate


def get_growing_system_types(db: Session) -> list[GrowingSystemType]:
    """Query and return all growing system types from the database."""
    return db.query(GrowingSystemType).all()


def get_growing_system_type(db: Session, growing_system_type_id: int) -> GrowingSystemType | None:
    """Return a single growing system type by ID, or None if not found."""
    return (
        db.query(GrowingSystemType).filter(GrowingSystemType.id == growing_system_type_id).first()
    )


def create_growing_system_type(db: Session, payload: GrowingSystemTypeCreate) -> GrowingSystemType:
    """Persist a new growing system type to the database and return it."""
    growing_system_type = GrowingSystemType(**payload.model_dump())
    db.add(growing_system_type)
    db.commit()
    db.refresh(growing_system_type)
    return growing_system_type


def update_growing_system_type(
    db: Session, growing_system_type: GrowingSystemType, payload: GrowingSystemTypeUpdate
) -> GrowingSystemType:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(growing_system_type, field, value)
    db.commit()
    db.refresh(growing_system_type)
    return growing_system_type


def delete_growing_system_type(db: Session, growing_system_type: GrowingSystemType) -> None:
    """Delete a growing system type from the database."""
    db.delete(growing_system_type)
    db.commit()
