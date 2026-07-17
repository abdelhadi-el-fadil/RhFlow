"""
Direction model — "directions" domain.
"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.domains.fiches_de_poste.model import FicheDePoste
    from app.domains.users.model import User


class Direction(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "directions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(nullable=True)
    director_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    director: Mapped["User | None"] = relationship("User", foreign_keys=[director_id])
    fiches: Mapped[list["FicheDePoste"]] = relationship(
        "FicheDePoste", back_populates="direction"
    )

    @property
    def director_name(self) -> str | None:
        if self.director is None:
            return None
        return self.director.full_name or self.director.email

    @property
    def fiche_count(self) -> int:
        return sum(1 for fiche in self.fiches if not fiche.is_deleted)
