"""
Sensor repository.
"""

from sqlalchemy.orm import Session

from app.models.sensors.sensor import Sensor
from app.repositories.base_repository import BaseRepository


class SensorRepository(BaseRepository[Sensor]):
    """
    Repository for Sensor database operations.
    """

    def __init__(self, db: Session):
        super().__init__(Sensor, db)
