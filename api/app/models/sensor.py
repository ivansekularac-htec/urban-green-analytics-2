"""
sensor.py
Sensor and sensor type models.
"""

from sqlalchemy import BigInteger, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import SensorStatus
from app.models.mixins import TimestampMixin


class SensorType(Base, TimestampMixin):
    """Model for different types of sensors."""

    __tablename__ = "sensor_types"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    unit: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(String(500))
    optimal_min: Mapped[float | None] = mapped_column(Numeric(10, 3))
    optimal_max: Mapped[float | None] = mapped_column(Numeric(10, 3))
    sensors: Mapped[list["Sensor"]] = relationship("Sensor", back_populates="sensor_type")


class Sensor(Base, TimestampMixin):
    """Model for sensors installed on farms."""

    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    farm_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False
    )
    sensor_type_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sensor_types.id"), nullable=False
    )
    serial_number: Mapped[str] = mapped_column(String(255), unique=True)
    status: Mapped[SensorStatus] = mapped_column(
        Enum(SensorStatus, name="sensor_status"),
        default=SensorStatus.ACTIVE,
    )
    installed_at: Mapped[int | None] = mapped_column(BigInteger)
    sensor_type: Mapped["SensorType"] = relationship("SensorType", back_populates="sensors")
    farm: Mapped["Farm"] = relationship("Farm", back_populates="sensors")
