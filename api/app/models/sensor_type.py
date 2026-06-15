from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models import TimestampMixin

if TYPE_CHECKING:
    from app.models.sensor import Sensor


class SensorType(TimestampMixin, Base):
    """ORM model representing a sensor measurement type."""

    __tablename__ = "sensor_types"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    optimal_min: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    optimal_max: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)

    sensors: Mapped[list[Sensor]] = relationship(back_populates="sensor_type")
