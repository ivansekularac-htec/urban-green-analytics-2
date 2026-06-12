"""This module defines the enumeration classes for sensor and farm statuses."""

from enum import StrEnum


class SensorStatus(StrEnum):
    ACTIVE = "ACTIVE"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"


class FarmStatus(StrEnum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    INACTIVE = "INACTIVE"
