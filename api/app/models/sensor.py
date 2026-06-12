"""
sensor.py
SQLAlchemy ORM model for the sensors table.

This module defines the Sensor entity and its relationships
to farms and sensor types.
"""

from sqlalchemy import (
    BigInteger,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import SensorStatus
from app.mixins import TimestampMixin
from app.models.farm import Farm
from app.models.sensor_type import SensorType


class Sensor(TimestampMixin, Base):
    """ORM model for the sensors table."""

    __tablename__ = "sensors"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    farm_id: Mapped[int] = mapped_column(
        ForeignKey("app.farms.id", ondelete="CASCADE"), nullable=False
    )
    sensor_type_id: Mapped[int] = mapped_column(ForeignKey("app.sensor_types.id"), nullable=False)

    serial_number: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    status: Mapped[SensorStatus] = mapped_column(
        Enum(SensorStatus, name="sensor_status"),
        nullable=False,
        default=SensorStatus.ACTIVE,
    )

    installed_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    farm: Mapped["Farm"] = relationship(
        back_populates="sensors",
    )

    sensor_type: Mapped["SensorType"] = relationship(
        back_populates="sensors",
    )
