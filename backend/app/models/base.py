"""
SQLAlchemy declarative Base + shared mixins (DRY) — used by every
model, in every domain.

Usage:
    class User(Base, TimestampMixin, SoftDeleteMixin):
        __tablename__ = "users"
        ...
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Adds created_at / updated_at, managed automatically by the DB."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Adds is_deleted / deleted_at for soft deletion."""

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )