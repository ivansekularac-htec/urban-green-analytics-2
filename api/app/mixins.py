from sqlalchemy import BigInteger, text
from sqlalchemy.orm import Mapped, mapped_column


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
