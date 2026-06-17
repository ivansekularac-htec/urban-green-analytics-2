from sqlalchemy.orm import Session

from app.models.sensors.sensor import Sensor
from app.schemas.sensors.sensor import SensorCreate, SensorUpdate


def get_sensors(db: Session) -> list[Sensor]:
    """Query and return all sensors from the database."""
    return db.query(Sensor).all()


def get_sensor(db: Session, sensor_id: int) -> Sensor | None:
    """Return a single sensor by ID, or None if not found."""
    return db.query(Sensor).filter(Sensor.id == sensor_id).first()


def create_sensor(db: Session, payload: SensorCreate) -> Sensor:
    """Persist a new sensor to the database and return it."""
    sensor = Sensor(**payload.model_dump())
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    return sensor


def update_sensor(db: Session, sensor: Sensor, payload: SensorUpdate) -> Sensor:
    """Apply partial field updates to an existing sensor and return it."""
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(sensor, field, value)
    db.commit()
    db.refresh(sensor)
    return sensor


def delete_sensor(db: Session, sensor: Sensor) -> None:
    """Delete a sensor from the database."""
    db.delete(sensor)
    db.commit()
