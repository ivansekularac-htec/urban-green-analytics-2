"""
farm.py
Farm model and related entities.
"""

from sqlalchemy import BigInteger, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import FarmStatus
from app.models.mixins import TimestampMixin


class Farm(Base, TimestampMixin):
    """Model for farms."""

    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    infrastructure_type_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("farm_infrastructure_types.id"),
        nullable=False,
    )
    growing_system_type_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("growing_system_types.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(255))
    size_m2: Mapped[float | None] = mapped_column(Numeric(10, 3))
    status: Mapped[FarmStatus] = mapped_column(
        Enum(FarmStatus, name="farm_status"),
        default=FarmStatus.ACTIVE,
    )
    growing_beds_count: Mapped[int | None] = mapped_column(Integer)
    infrastructure_type: Mapped["FarmInfrastructureType"] = relationship(
        "FarmInfrastructureType", back_populates="farms"
    )
    growing_system_type: Mapped["GrowingSystemType"] = relationship(
        "GrowingSystemType", back_populates="farms"
    )
    sensors: Mapped[list["Sensor"]] = relationship("Sensor", back_populates="farm")
    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="farm")
    farm_crops: Mapped[list["FarmCrop"]] = relationship("FarmCrop", back_populates="farm")
    harvests: Mapped[list["Harvest"]] = relationship("Harvest", back_populates="farm")
