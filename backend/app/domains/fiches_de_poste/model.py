"""Fiche de poste model."""
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domains.directions.model import Direction
from app.domains.fiches_de_poste.enums import FicheStatus
from app.domains.users.model import User
from app.models.base import AuditMixin, Base, SoftDeleteMixin, TimestampMixin


class FicheDePoste(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "fiches_de_poste"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    missions: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[str] = mapped_column(Text, nullable=False)
    experience_level: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[FicheStatus] = mapped_column(
        SQLEnum(FicheStatus, name="fichestatus"),
        default=FicheStatus.DRAFT,
        server_default=text("'DRAFT'"),
        nullable=False,
    )
    direction_id: Mapped[int] = mapped_column(
        ForeignKey("directions.id"),
        nullable=False,
    )
    validated_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    direction: Mapped[Direction] = relationship()
    validated_by: Mapped[User | None] = relationship(foreign_keys=[validated_by_id])
