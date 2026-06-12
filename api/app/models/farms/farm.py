"""
Farm ORM model.

Represents an agricultural production unit that uses a specific
infrastructure and growing system, and serves as the central
entity for crops, sensors, and harvest tracking.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.audit import AuditMixin
from app.models.farms.farm_status import FarmStatus

if TYPE_CHECKING:
    from app.models.crops.farm_crop import FarmCrop
    from app.models.farms.growing_system_type import GrowingSystemType
    from app.models.farms.infrastructure_type import InfrastructureType
    from app.models.harvests.harvest import Harvest
    from app.models.sensors.sensor import Sensor
    from app.models.users.user_roles import UserRole


class Farm(Base, AuditMixin):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    infrastructure_type_id: Mapped[int] = mapped_column(
        ForeignKey("farm_infrastructure_types.id"),
        nullable=False,
    )

    growing_system_type_id: Mapped[int] = mapped_column(
        ForeignKey("growing_system_types.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    city: Mapped[str | None] = mapped_column(
        String(255),
    )

    size_m2: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3),
    )

    status: Mapped[FarmStatus] = mapped_column(
        Enum(FarmStatus),
        nullable=False,
        default=FarmStatus.ACTIVE,
    )

    growing_beds_count: Mapped[int | None] = mapped_column(
        Integer,
    )

    # ------------------------------------------------------
    # Relationships
    # ------------------------------------------------------

    user_roles: Mapped[list[UserRole]] = relationship(
        back_populates="farm",
    )

    infrastructure_type: Mapped[InfrastructureType] = relationship(
        back_populates="farms",
    )

    growing_system_type: Mapped[GrowingSystemType] = relationship(
        back_populates="farms",
    )

    sensors: Mapped[list[Sensor]] = relationship(
        back_populates="farm",
    )

    farm_crops: Mapped[list[FarmCrop]] = relationship(
        back_populates="farm",
    )

    harvests: Mapped[list[Harvest]] = relationship(
        back_populates="farm",
    )
