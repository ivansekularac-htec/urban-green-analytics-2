from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models import TimestampMixin

if TYPE_CHECKING:
    from app.models.farm import Farm
    from app.models.role import Role
    from app.models.user import User


class UserRole(TimestampMixin, Base):
    """ORM model representing a user's assigned role, optionally scoped to a farm."""

    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", "farm_id", name="uq_user_role_farm"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    farm_id: Mapped[int | None] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=True,
    )

    user: Mapped[User] = relationship(back_populates="user_roles")
    role: Mapped[Role] = relationship(back_populates="user_roles")
    farm: Mapped[Farm | None] = relationship(back_populates="user_roles")
