"""add project links and nombre postes

Revision ID: 7b82c3a4d9ef
Revises: 5f4b2a3c9d10
Create Date: 2026-07-08 19:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7b82c3a4d9ef"
down_revision: Union[str, Sequence[str], None] = "5f4b2a3c9d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projets_recrutement", sa.Column("besoin_recrutement_id", sa.Integer(), nullable=True))
    op.add_column("projets_recrutement", sa.Column("fiche_de_poste_id", sa.Integer(), nullable=True))
    op.add_column("projets_recrutement", sa.Column("nombre_postes", sa.Integer(), nullable=True))

    op.create_foreign_key(
        "fk_proj_besoin_id",
        "projets_recrutement",
        "besoins_recrutement",
        ["besoin_recrutement_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_proj_fiche_id",
        "projets_recrutement",
        "fiches_de_poste",
        ["fiche_de_poste_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_proj_besoin_id",
        "projets_recrutement",
        ["besoin_recrutement_id"],
    )

    op.execute(
        """
        UPDATE projets_recrutement AS p
        SET besoin_recrutement_id = src.id,
            fiche_de_poste_id = src.fiche_de_poste_id,
            nombre_postes = src.positions_count
        FROM (
            SELECT DISTINCT ON (projet_id)
                id,
                projet_id,
                fiche_de_poste_id,
                positions_count
            FROM besoins_recrutement
            WHERE projet_id IS NOT NULL
            ORDER BY projet_id, id
        ) AS src
        WHERE p.id = src.projet_id
        """
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_proj_besoin_id",
        "projets_recrutement",
        type_="unique",
    )
    op.drop_constraint(
        "fk_proj_fiche_id",
        "projets_recrutement",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_proj_besoin_id",
        "projets_recrutement",
        type_="foreignkey",
    )
    op.drop_column("projets_recrutement", "nombre_postes")
    op.drop_column("projets_recrutement", "fiche_de_poste_id")
    op.drop_column("projets_recrutement", "besoin_recrutement_id")