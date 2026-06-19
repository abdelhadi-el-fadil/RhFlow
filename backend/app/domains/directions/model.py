"""
Direction model — "directions" domain.
"""
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditMixin, Base, SoftDeleteMixin, TimestampMixin


class Direction(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "directions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(nullable=True)
    director_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
