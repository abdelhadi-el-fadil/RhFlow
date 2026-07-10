"""
User model — "users" domain.

Represents an application user account.
"""
from sqlalchemy import Boolean, String, text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import UserRole
from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gsm: Mapped[str | None] = mapped_column(String(20), nullable=True)
    signature_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    signature_content_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="userrole"),
        nullable=False,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
    )

    managed_projects = relationship("ProjetRecrutement",
                                    foreign_keys="ProjetRecrutement.manager_id")