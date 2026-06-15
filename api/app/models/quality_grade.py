from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models import TimestampMixin

if TYPE_CHECKING:
    from app.models.harvest import Harvest


class QualityGrade(TimestampMixin, Base):
    """ORM model representing a harvest quality grade."""

    __tablename__ = "quality_grades"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    harvests: Mapped[list[Harvest]] = relationship(back_populates="quality_grade")
