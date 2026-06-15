"""
SensorType ORM model.

Defines types of sensors used in farms, including measurement unit
and optimal operating range for each sensor type.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.audit import AuditMixin

if TYPE_CHECKING:
    from app.models.sensors.sensor import Sensor


class SensorType(Base, AuditMixin):
    __tablename__ = "sensor_types"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
    )

    optimal_min: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3),
    )

    optimal_max: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3),
    )

    # ------------------------------------------------------
    # Relationships
    # ------------------------------------------------------

    sensors: Mapped[list[Sensor]] = relationship(
        back_populates="sensor_type",
    )
