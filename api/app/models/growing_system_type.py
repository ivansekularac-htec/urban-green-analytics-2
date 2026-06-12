"""
growing_system_type.py
SQLAlchemy ORM model for the growing_system_types table.

This module defines the GrowingSystemType lookup entity
used to categorize farm growing systems.
"""

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import TIMESTAMP_DEFAULT

if TYPE_CHECKING:
    from app.models.farm import Farm


class GrowingSystemType(Base):
    """ORM model for the growing_system_types table."""

    __tablename__ = "growing_system_types"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=TIMESTAMP_DEFAULT
    )
    updated_at: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=TIMESTAMP_DEFAULT
    )

    farms: Mapped[list["Farm"]] = relationship(back_populates="growing_system_type")
