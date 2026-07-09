"""Recruitment models."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, String, text
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
    besoin_recrutement_id: Mapped[int | None] = mapped_column(
        ForeignKey("besoins_recrutement.id"),
        unique=True,
        nullable=True,
    )
    fiche_de_poste_id: Mapped[int | None] = mapped_column(
        ForeignKey("fiches_de_poste.id"),
        nullable=True,
    )
    nombre_postes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    email_subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manager: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[manager_id],
        overlaps="managed_projects",
    )
    besoins: Mapped[list[BesoinRecrutement]] = relationship(
        back_populates="projet",
        foreign_keys="BesoinRecrutement.projet_id",
    )
    besoin_recrutement: Mapped[BesoinRecrutement | None] = relationship(
        foreign_keys=[besoin_recrutement_id],
        post_update=True,
    )
    fiche_de_poste: Mapped[FicheDePoste | None] = relationship(
        foreign_keys=[fiche_de_poste_id],
        overlaps="recruitment_projects",
    )

    @property
    def manager_name(self) -> str | None:
        manager = self.manager
        if manager is None:
            return None
        return manager.full_name or manager.email

    @property
    def fiche_title(self) -> str | None:
        return self.fiche_de_poste.title if self.fiche_de_poste else None

    @property
    def besoin_title(self) -> str | None:
        return self.besoin_recrutement.title if self.besoin_recrutement else None

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


class BesoinRecrutement(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "besoins_recrutement"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
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
    fiche_de_poste: Mapped[FicheDePoste] = relationship(
    foreign_keys=[fiche_de_poste_id]
)
    projet: Mapped[ProjetRecrutement | None] = relationship(
        back_populates="besoins",
        foreign_keys=[projet_id],
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
        return self.description

    @property
    def recruitment_reason(self) -> str | None:
        return self.justification