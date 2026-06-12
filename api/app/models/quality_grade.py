"""
quality_grade.py
SQLAlchemy ORM model for the quality_grades table.

This module defines the QualityGrade lookup entity used
to classify harvested crops by quality.
"""

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common import TIMESTAMP_DEFAULT

if TYPE_CHECKING:
    from app.models.harvest import Harvest


class QualityGrade(Base):
    """ORM model for the quality_grades table."""

    __tablename__ = "quality_grades"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=TIMESTAMP_DEFAULT
    )
    updated_at: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=TIMESTAMP_DEFAULT
    )

    harvests: Mapped[list["Harvest"]] = relationship(back_populates="quality_grade")
