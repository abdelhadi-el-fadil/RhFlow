"""Offre model."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domains.offres.enums import OffreStatus
from app.domains.recruitment.model import BesoinRecrutement
from app.domains.users.model import User
from app.models.base import AuditMixin, Base, SoftDeleteMixin, TimestampMixin


class Offre(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "offres"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    requirements: Mapped[str | None] = mapped_column(nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[OffreStatus] = mapped_column(
        SQLEnum(OffreStatus, name="offrestatus"),
        default=OffreStatus.DRAFT,
        server_default=text("'DRAFT'"),
        nullable=False,
    )
    besoin_id: Mapped[int] = mapped_column(
        ForeignKey("besoins_recrutement.id"),
        nullable=False,
    )
    published_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    besoin: Mapped[BesoinRecrutement] = relationship()
    published_by: Mapped[User | None] = relationship(foreign_keys=[published_by_id])
