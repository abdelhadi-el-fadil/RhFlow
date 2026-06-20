"""add besoin fiche foreign key

Revision ID: d7a41c9f6b2e
Revises: c1f8d3a4b7e1
Create Date: 2026-06-19 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "d7a41c9f6b2e"
down_revision: Union[str, Sequence[str], None] = "c1f8d3a4b7e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_besoins_recrutement_fiche_de_poste_id_fiches_de_poste",
        "besoins_recrutement",
        "fiches_de_poste",
        ["fiche_de_poste_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_besoins_recrutement_fiche_de_poste_id_fiches_de_poste",
        "besoins_recrutement",
        type_="foreignkey",
    )
