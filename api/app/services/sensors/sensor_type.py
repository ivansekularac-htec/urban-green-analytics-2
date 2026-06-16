from sqlalchemy.orm import Session

from app.models.sensors.sensor_type import SensorType
from app.schemas.sensors.sensor_type import SensorTypeCreate, SensorTypeUpdate


def get_sensor_types(db: Session) -> list[SensorType]:
    """Query and return all sensor types from the database."""
    return db.query(SensorType).all()


def get_sensor_type(db: Session, sensor_type_id: int) -> SensorType | None:
    """Return a single sensor type by ID, or None if not found."""
    return db.query(SensorType).filter(SensorType.id == sensor_type_id).first()


def create_sensor_type(db: Session, payload: SensorTypeCreate) -> SensorType:
    """Persist a new sensor type to the database and return it."""
    sensor_type = SensorType(**payload.model_dump())
    db.add(sensor_type)
    db.commit()
    db.refresh(sensor_type)
    return sensor_type


def update_sensor_type(
    db: Session, sensor_type: SensorType, payload: SensorTypeUpdate
) -> SensorType:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(sensor_type, field, value)
    db.commit()
    db.refresh(sensor_type)
    return sensor_type


def delete_sensor_type(db: Session, sensor_type: SensorType) -> None:
    """Delete a sensor type from the database."""
    db.delete(sensor_type)
    db.commit()
