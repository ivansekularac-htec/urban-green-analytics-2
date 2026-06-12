"""
role.py
Role model for user permissions and access control.
"""

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class Role(Base, TimestampMixin):
    """User role model for defining permissions and access levels."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(String(500))
    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="role")
