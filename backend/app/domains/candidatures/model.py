"""Candidature model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domains.candidatures.enums import CandidatureStatut, RecommandationIA
from app.domains.candidatures.error_messages import humanize_candidature_error
from app.models.base import AuditMixin, Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.domains.recruitment.model import ProjetRecrutement


class Candidature(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "candidatures"
    __table_args__ = (
        Index(
            "uq_candidatures_projet_email_candidat_active",
            "projet_recrutement_id",
            "email_candidat",
            unique=True,
            postgresql_where=text("is_deleted = false AND email_candidat IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    projet_recrutement_id: Mapped[int] = mapped_column(
        ForeignKey("projets_recrutement.id"),
        nullable=False,
    )

    nom_fichier: Mapped[str] = mapped_column(String(255), nullable=False)
    chemin_minio: Mapped[str] = mapped_column(String(512), nullable=False)
    type_fichier: Mapped[str] = mapped_column(String(128), nullable=False)
    taille_fichier: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contenu_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)

    nom_candidat: Mapped[str | None] = mapped_column(String(200), nullable=True)
    email_candidat: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telephone_candidat: Mapped[str | None] = mapped_column(String(50), nullable=True)
    formations: Mapped[list[dict[str, str]] | None] = mapped_column(JSON, nullable=True)
    experiences: Mapped[list[dict[str, str]] | None] = mapped_column(
        JSON, nullable=True
    )
    skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    score_matching: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points_forts: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    points_manquants: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    recommandation: Mapped[RecommandationIA | None] = mapped_column(
        SQLEnum(RecommandationIA, name="recommandationia"),
        nullable=True,
    )
    justification_ia: Mapped[str | None] = mapped_column(Text, nullable=True)
    questions_entretien: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    statut: Mapped[CandidatureStatut] = mapped_column(
        SQLEnum(CandidatureStatut, name="candidaturestatut"),
        default=CandidatureStatut.RECU,
        server_default=text("'RECU'"),
        nullable=False,
    )
    depose_le: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    evalue_le: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )

    __mapper_args__ = {"version_id_col": version}

    projet_recrutement: Mapped[ProjetRecrutement] = relationship(
        "ProjetRecrutement",
        back_populates="candidatures",
    )

    @property
    def projet_title(self) -> str | None:
        projet = self.projet_recrutement
        if projet is None:
            return None
        return getattr(projet, "title", None)

    @property
    def error_summary(self) -> str | None:
        if self.statut != CandidatureStatut.ERREUR:
            return None
        if self.justification_ia and "\n\nDetail technique: " in self.justification_ia:
            return self.justification_ia.split("\n\nDetail technique: ", maxsplit=1)[0]
        return humanize_candidature_error(self.justification_ia)

    @property
    def error_detail(self) -> str | None:
        if self.statut != CandidatureStatut.ERREUR:
            return None
        if self.justification_ia and "\n\nDetail technique: " in self.justification_ia:
            return self.justification_ia.split("\n\nDetail technique: ", maxsplit=1)[1]
        return self.justification_ia
