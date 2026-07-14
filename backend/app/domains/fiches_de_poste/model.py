"""Fiche de poste model."""
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domains.directions.model import Direction
from app.domains.users.model import User
from app.models.base import AuditMixin, Base, SoftDeleteMixin, TimestampMixin


class FicheDePoste(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "fiches_de_poste"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    main_activities: Mapped[str] = mapped_column(Text, nullable=False)
    missions: Mapped[str] = mapped_column(Text, nullable=False)
    experience_level: Mapped[str] = mapped_column(String(100), nullable=False)
    formation_domain: Mapped[str | None] = mapped_column(String(150), nullable=True)
    education_level: Mapped[str | None] = mapped_column(String(100), nullable=True)
    technical_skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    managerial_skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    direction_id: Mapped[int] = mapped_column(
        ForeignKey("directions.id"),
        nullable=False,
    )
    validated_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    direction: Mapped[Direction] = relationship(back_populates="fiches")
    validated_by: Mapped[User | None] = relationship(foreign_keys=[validated_by_id])

    @property
    def direction_name(self) -> str | None:
        return self.direction.name if self.direction else None
