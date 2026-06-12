from enum import StrEnum


class FarmStatus(StrEnum):
    """Enumeration of supported farm lifecycle statuses."""

    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    INACTIVE = "INACTIVE"


class SensorStatus(StrEnum):
    """Enumeration of supported sensor lifecycle statuses."""

    ACTIVE = "ACTIVE"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"
