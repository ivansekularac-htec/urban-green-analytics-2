"""
Sensor type service.
"""

from app.models.sensors.sensor_type import SensorType
from app.repositories.sensors.sensor_type_repository import SensorTypeRepository
from app.schemas.sensors.sensor_type import SensorTypeCreate, SensorTypeUpdate
from app.services.base_service import BaseService


class SensorTypeService(BaseService[SensorType, SensorTypeCreate, SensorTypeUpdate]):
    """
    Service for SensorType business logic.
    """

    def __init__(self, repository: SensorTypeRepository):
        super().__init__(repository, "Sensor type")
