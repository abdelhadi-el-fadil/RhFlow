"""Recruitment models."""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domains.recruitment.enums import BesoinStatus, ProjetStatus
from app.models.base import AuditMixin, Base, SoftDeleteMixin, TimestampMixin


class ProjetRecrutement(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "projets_recrutement"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ProjetStatus] = mapped_column(
        SQLEnum(ProjetStatus, name="projetstatus"),
        default=ProjetStatus.DRAFT,
        server_default=text("'DRAFT'"),
        nullable=False,
    )
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    besoins: Mapped[list[BesoinRecrutement]] = relationship(back_populates="projet")


class BesoinRecrutement(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "besoins_recrutement"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    positions_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    desired_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    justification: Mapped[str | None] = mapped_column(nullable=True)
    status: Mapped[BesoinStatus] = mapped_column(
        SQLEnum(BesoinStatus, name="besoinstatus"),
        default=BesoinStatus.DRAFT,
        server_default=text("'DRAFT'"),
        nullable=False,
    )
    rejection_reason: Mapped[str | None] = mapped_column(nullable=True)
    fiche_de_poste_id: Mapped[int] = mapped_column(
        ForeignKey("fiches_de_poste.id"),
        nullable=False,
    )
    submitted_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
    processed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
    projet_id: Mapped[int | None] = mapped_column(
        ForeignKey("projets_recrutement.id"),
        nullable=True,
    )
    projet: Mapped[ProjetRecrutement | None] = relationship(back_populates="besoins")
