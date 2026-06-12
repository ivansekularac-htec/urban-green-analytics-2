"""
sensor_type.py
SQLAlchemy ORM model for the sensor_types table.

This module defines the SensorType lookup entity used
to classify sensors and their measurement characteristics.
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import TimestampMixin

if TYPE_CHECKING:
    from app.models.sensor import Sensor


class SensorType(Base, TimestampMixin):
    """ORM model for the sensor_types table."""

    __tablename__ = "sensor_types"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    optimal_min: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    optimal_max: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))

    sensors: Mapped[list["Sensor"]] = relationship(back_populates="sensor_type")
