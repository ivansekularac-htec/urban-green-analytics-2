from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class QualityGrade(Base, TimestampMixin):
    __tablename__ = "quality_grades"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

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

    harvests: Mapped[list["Harvest"]] = relationship(back_populates="quality_grade")
