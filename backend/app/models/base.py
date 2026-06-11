"""
Base déclarative SQLAlchemy + mixins partagés (DRY) — utilisés par tous
les modèles, dans tous les domaines.

Usage :
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
    """Ajoute created_at / updated_at, gérés automatiquement par la DB."""

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
    """Ajoute is_deleted / deleted_at pour la suppression logique."""

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )