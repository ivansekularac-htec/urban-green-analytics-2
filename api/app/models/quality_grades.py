from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.helpers import get_current_timestamp

class QualityGrade(Base):
    """Model representing a quality grade for harvested crops."""

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
        nullable=True,
    )

    created_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=get_current_timestamp,
    )

    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=get_current_timestamp,
        onupdate=get_current_timestamp,
    )

    harvests: Mapped[list["Harvest"]] = relationship(
        back_populates="quality_grade",
    )