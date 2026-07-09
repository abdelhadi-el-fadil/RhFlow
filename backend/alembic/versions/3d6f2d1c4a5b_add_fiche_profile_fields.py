"""add fiche profile fields

Revision ID: 3d6f2d1c4a5b
Revises: c1f8d3a4b7e1
Create Date: 2026-07-08 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3d6f2d1c4a5b"
down_revision: Union[str, Sequence[str], None] = "c1f8d3a4b7e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "fiches_de_poste",
        sa.Column("formation_domain", sa.String(length=150), nullable=True),
    )
    op.add_column(
        "fiches_de_poste",
        sa.Column("education_level", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "fiches_de_poste",
        sa.Column("technical_skills", sa.Text(), nullable=True),
    )
    op.add_column(
        "fiches_de_poste",
        sa.Column("managerial_skills", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("fiches_de_poste", "managerial_skills")
    op.drop_column("fiches_de_poste", "technical_skills")
    op.drop_column("fiches_de_poste", "education_level")
    op.drop_column("fiches_de_poste", "formation_domain")
