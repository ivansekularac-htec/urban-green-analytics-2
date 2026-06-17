"""
Sensor ORM model.

Represents a physical sensor installed on a farm, used to collect
environmental or production-related measurements based on its sensor type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common.audit import AuditMixin
from app.models.sensors.sensor_status import SensorStatus

if TYPE_CHECKING:
    from app.models.farms.farm import Farm
    from app.models.sensors.sensor_type import SensorType


class Sensor(Base, AuditMixin):
    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    farm_id: Mapped[int] = mapped_column(
        ForeignKey(
            "farms.id",
            ondelete="CASCADE",
        )
    )

    sensor_type_id: Mapped[int] = mapped_column(
        ForeignKey("sensor_types.id"),
    )

    serial_number: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    status: Mapped[SensorStatus] = mapped_column(
        Enum(SensorStatus),
        nullable=False,
        default=SensorStatus.ACTIVE,
    )

    installed_at: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    # ------------------------------------------------------
    # Relationships
    # ------------------------------------------------------

    farm: Mapped[Farm] = relationship(
        back_populates="sensors",
    )

    sensor_type: Mapped[SensorType] = relationship(
        back_populates="sensors",
    )
