"""
enums.py
Enumeration types used across the application.
"""

from enum import StrEnum


class FarmStatus(StrEnum):
    """Status enum for farms."""

    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    INACTIVE = "INACTIVE"


class SensorStatus(StrEnum):
    """Status enum for sensors."""

    ACTIVE = "ACTIVE"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"
