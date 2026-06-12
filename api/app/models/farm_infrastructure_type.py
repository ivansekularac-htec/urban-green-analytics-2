"""
farm_infrastructure_type.py
SQLAlchemy ORM model for the farm_infrastructure_types table.

This module defines the FarmInfrastructureType lookup entity
used to categorize farm infrastructure configurations.
"""

from sqlalchemy import (
    BigInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.mixins import TimestampMixin
from app.models.farm import Farm


class FarmInfrastructureType(TimestampMixin, Base):
    """ORM model for the farm_infrastructure_types table."""

    __tablename__ = "farm_infrastructure_types"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    farms: Mapped[list["Farm"]] = relationship(
        back_populates="infrastructure_type",
    )
