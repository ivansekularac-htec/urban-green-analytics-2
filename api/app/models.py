from sqlalchemy import BigInteger, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TimestampMixin:
    """Common timestamp fields for database entities."""

    created_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=text("(EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT)"),
    )

    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=text("(EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT)"),
    )


class Role(TimestampMixin, Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
