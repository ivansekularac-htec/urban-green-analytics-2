"""
Sensor type repository.
"""

from sqlalchemy.orm import Session

from app.models.sensors.sensor_type import SensorType
from app.repositories.base_repository import BaseRepository


class SensorTypeRepository(BaseRepository[SensorType]):
    """
    Repository for SensorType database operations.
    """

    def __init__(self, db: Session):
        super().__init__(SensorType, db)
