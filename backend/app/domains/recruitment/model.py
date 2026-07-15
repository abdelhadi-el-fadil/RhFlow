"""Recruitment models."""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domains.fiches_de_poste.model import FicheDePoste
from app.domains.recruitment.enums import BesoinPriority, BesoinStatus, ProjetStatus
from app.models.base import AuditMixin, Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.domains.fiches_de_poste.model import FicheDePoste
    from app.domains.users.model import User


class ProjetRecrutement(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "projets_recrutement"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[ProjetStatus] = mapped_column(
        SQLEnum(ProjetStatus, name="projetstatus"),
        default=ProjetStatus.ACTIVE,
        server_default=text("'ACTIVE'"),
        nullable=False,
    )
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    besoin_recrutement_id: Mapped[int] = mapped_column(
        ForeignKey("besoins_recrutement.id"),
        unique=True,
        nullable=False,
    )
    email_subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    offre: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    manager: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[manager_id],
        overlaps="managed_projects",
    )
    besoin_recrutement: Mapped[BesoinRecrutement] = relationship(
        foreign_keys=[besoin_recrutement_id]
    )

    @property
    def manager_name(self) -> str | None:
        manager = self.manager
        if manager is None:
            return None
        return manager.full_name or manager.email

    @property
    def fiche_title(self) -> str | None:
        besoin = self.besoin_recrutement
        fiche = besoin.fiche_de_poste if besoin else None
        return fiche.title if fiche else None

    @property
    def besoin_title(self) -> str | None:
        return self.fiche_title

    @property
    def nombre_postes(self) -> int | None:
        besoin = self.besoin_recrutement
        return besoin.positions_count if besoin else None

    @property
    def title(self) -> str:
        fiche_title = self.fiche_title or "Poste"
        return f"Recrutement - {fiche_title}"

    @property
    def direction_name(self) -> str | None:
        besoin = self.besoin_recrutement
        fiche = besoin.fiche_de_poste if besoin else None
        return fiche.direction_name if fiche else None

    @property
    def director_name(self) -> str | None:
        besoin = self.besoin_recrutement
        fiche = besoin.fiche_de_poste if besoin else None
        direction = fiche.direction if fiche else None
        director = direction.director if direction else None
        if director is None:
            return None
        return director.full_name or director.email


class BesoinRecrutement(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "besoins_recrutement"

    id: Mapped[int] = mapped_column(primary_key=True)
    lieu_affectation: Mapped[str] = mapped_column(String(255), nullable=False)
    positions_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    desired_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    justification: Mapped[str | None] = mapped_column(nullable=True)
    priority: Mapped[BesoinPriority] = mapped_column(
        SQLEnum(BesoinPriority, name="besoinpriority"),
        default=BesoinPriority.NORMALE,
        server_default=text("'NORMALE'"),
        nullable=False,
    )
    status: Mapped[BesoinStatus] = mapped_column(
        SQLEnum(BesoinStatus, name="besoinstatus"),
        default=BesoinStatus.SUBMITTED,
        server_default=text("'SUBMITTED'"),
        nullable=False,
    )
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
    fiche_de_poste: Mapped[FicheDePoste] = relationship(
        foreign_keys=[fiche_de_poste_id]
    )
    submitted_by: Mapped[User | None] = relationship(foreign_keys=[submitted_by_id])
    processed_by: Mapped[User | None] = relationship(foreign_keys=[processed_by_id])

    @property
    def fiche_title(self) -> str | None:
        fiche = self.fiche_de_poste
        return fiche.title if fiche else None

    @property
    def direction_name(self) -> str | None:
        fiche = self.fiche_de_poste
        return fiche.direction_name if fiche else None

    @property
    def director_name(self) -> str | None:
        fiche = self.fiche_de_poste
        direction = fiche.direction if fiche else None
        director = direction.director if direction else None
        if director is None:
            return None
        return director.full_name or director.email

    @property
    def requester_name(self) -> str | None:
        author = self.submitted_by
        if author is None:
            return None
        return author.full_name or author.email

    @property
    def location(self) -> str | None:
        return self.lieu_affectation

    @property
    def recruitment_reason(self) -> str | None:
        return self.justification