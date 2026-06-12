"""
user.py
User and user role models.
"""

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class User(Base, TimestampMixin):
    """Model for users of the application."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="user")


class UserRole(Base, TimestampMixin):
    """Model for mapping users to roles on farms."""

    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("roles.id"),
        nullable=False,
    )
    farm_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=True,
    )
    user: Mapped["User"] = relationship("User", back_populates="user_roles")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")
    farm: Mapped["Farm | None"] = relationship("Farm", back_populates="user_roles")

    __table_args__ = (UniqueConstraint("user_id", "role_id", "farm_id", name="uq_user_role_farm"),)
