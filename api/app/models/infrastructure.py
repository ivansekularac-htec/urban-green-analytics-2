"""
infrastructure.py
Farm infrastructure and growing system type models.
"""

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class FarmInfrastructureType(Base, TimestampMixin):
    """Model for different types of farm infrastructure."""

    __tablename__ = "farm_infrastructure_types"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(String(500))
    farms: Mapped[list["Farm"]] = relationship("Farm", back_populates="infrastructure_type")


class GrowingSystemType(Base, TimestampMixin):
    """Model for different types of growing systems."""

    __tablename__ = "growing_system_types"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(String(500))
    farms: Mapped[list["Farm"]] = relationship("Farm", back_populates="growing_system_type")
