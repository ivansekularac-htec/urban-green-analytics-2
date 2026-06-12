from enum import Enum


class FarmStatus(str, Enum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    INACTIVE = "INACTIVE"


class SensorStatus(str, Enum):
    ACTIVE = "ACTIVE"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"
