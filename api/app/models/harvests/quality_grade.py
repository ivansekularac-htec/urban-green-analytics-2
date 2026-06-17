"""
QualityGrade ORM model.

Represents the quality classification assigned to harvested crops,
used to evaluate and categorize harvest output.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.common.audit import AuditMixin

if TYPE_CHECKING:
    from app.models.harvests.harvest import Harvest


class QualityGrade(Base, AuditMixin):
    __tablename__ = "quality_grades"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
    )

    # ------------------------------------------------------
    # Relationships
    # ------------------------------------------------------

    harvests: Mapped[list[Harvest]] = relationship(
        back_populates="quality_grade",
    )
