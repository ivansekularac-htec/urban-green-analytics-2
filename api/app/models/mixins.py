from sqlalchemy import BigInteger, text
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
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
