"""
farm.py
SQLAlchemy ORM model for the farms table.

This module defines the Farm entity and its relationships
to infrastructure types, growing systems, sensors,
harvests, crops, and user assignments.
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import FarmStatus
from app.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.farm_crop import FarmCrop
    from app.models.farm_infrastructure_type import FarmInfrastructureType
    from app.models.growing_system_type import GrowingSystemType
    from app.models.harvest import Harvest
    from app.models.sensor import Sensor
    from app.models.user_role import UserRole


class Farm(TimestampMixin, Base):
    """ORM model for the farms table."""

    __tablename__ = "farms"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    infrastructure_type_id: Mapped[int] = mapped_column(
        ForeignKey("app.farm_infrastructure_types.id"), nullable=False
    )
    growing_system_type_id: Mapped[int] = mapped_column(
        ForeignKey("app.growing_system_types.id"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str | None] = mapped_column(String(255))

    size_m2: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )

    status: Mapped[FarmStatus] = mapped_column(
        Enum(FarmStatus, name="farm_status"),
        nullable=False,
        default=FarmStatus.ACTIVE,
    )

    growing_beds_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    sensors: Mapped[list["Sensor"]] = relationship(
        back_populates="farm",
    )

    harvests: Mapped[list["Harvest"]] = relationship(
        back_populates="farm",
    )

    infrastructure_type: Mapped["FarmInfrastructureType"] = relationship(
        back_populates="farms",
    )

    growing_system_type: Mapped["GrowingSystemType"] = relationship(
        back_populates="farms",
    )

    user_roles: Mapped[list["UserRole"]] = relationship(
        back_populates="farm",
    )

    farm_crops: Mapped[list["FarmCrop"]] = relationship(
        back_populates="farm",
    )
