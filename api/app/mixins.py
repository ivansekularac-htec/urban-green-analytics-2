from time import time

from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    created_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=lambda: int(time()),
    )

    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=lambda: int(time()),
        onupdate=lambda: int(time()),
    )
