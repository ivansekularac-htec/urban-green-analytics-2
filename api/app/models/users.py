from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.helpers import get_current_timestamp


class User(Base):
    """User model representing a user in the system."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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

    user_roles: Mapped[list["UserRole"]] = relationship(
        back_populates="user",
    )