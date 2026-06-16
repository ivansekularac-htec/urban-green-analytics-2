"""
Sensor service.
"""

from app.models.sensors.sensor import Sensor
from app.repositories.sensors.sensor_repository import SensorRepository
from app.schemas.sensors.sensor import SensorCreate, SensorUpdate
from app.services.base_service import BaseService


class SensorService(BaseService[Sensor, SensorCreate, SensorUpdate]):
    """
    Service for Sensor business logic.
    """

    def __init__(self, repository: SensorRepository):
        super().__init__(repository, "Sensor")
