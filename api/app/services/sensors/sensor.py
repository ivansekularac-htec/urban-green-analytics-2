"""
Sensor service.
"""

from app.models.sensors.sensor import Sensor
from app.models.users.user import User
from app.repositories.sensors.sensor import SensorRepository
from app.schemas.sensors.sensor import SensorCreate, SensorUpdate
from app.services.scoped_service import ScopedService


class SensorService(ScopedService[Sensor, SensorCreate, SensorUpdate]):
    """
    Service for Sensor business logic.
    """

    def __init__(self, repository: SensorRepository, current_user: User):
        super().__init__(repository, "Sensor", current_user)
