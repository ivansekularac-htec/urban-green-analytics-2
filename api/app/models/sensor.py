from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models import TimestampMixin
from app.models.enums import SensorStatus

if TYPE_CHECKING:
    from app.models.farm import Farm
    from app.models.sensor_type import SensorType


class Sensor(TimestampMixin, Base):
    """ORM model representing a physical sensor installed on a farm."""

    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
    )
    sensor_type_id: Mapped[int] = mapped_column(
        ForeignKey("sensor_types.id"),
        nullable=False,
    )
    serial_number: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    status: Mapped[SensorStatus] = mapped_column(
        ENUM(SensorStatus, name="sensor_status"),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )
    installed_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    farm: Mapped[Farm] = relationship(back_populates="sensors")
    sensor_type: Mapped[SensorType] = relationship(back_populates="sensors")
