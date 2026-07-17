"""create candidatures table

Revision ID: d9b3f1a2c4e5
Revises: 6c138b22aaea
Create Date: 2026-07-16 16:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d9b3f1a2c4e5"
down_revision: Union[str, Sequence[str], None] = "6c138b22aaea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "candidatures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("projet_recrutement_id", sa.Integer(), nullable=False),
        sa.Column("nom_fichier", sa.String(length=255), nullable=False),
        sa.Column("chemin_minio", sa.String(length=512), nullable=False),
        sa.Column("type_fichier", sa.String(length=128), nullable=False),
        sa.Column("taille_fichier", sa.Integer(), nullable=True),
        sa.Column("nom_candidat", sa.String(length=200), nullable=True),
        sa.Column("email_candidat", sa.String(length=255), nullable=True),
        sa.Column("telephone_candidat", sa.String(length=50), nullable=True),
        sa.Column("formations", sa.JSON(), nullable=True),
        sa.Column("experiences", sa.JSON(), nullable=True),
        sa.Column("score_matching", sa.Integer(), nullable=True),
        sa.Column("points_forts", sa.JSON(), nullable=True),
        sa.Column("points_manquants", sa.JSON(), nullable=True),
        sa.Column(
            "recommandation",
            sa.Enum(
                "A_CONVOQUER",
                "A_ETUDIER",
                "NE_CORRESPOND_PAS",
                name="recommandationia",
            ),
            nullable=True,
        ),
        sa.Column("justification_ia", sa.Text(), nullable=True),
        sa.Column("questions_entretien", sa.JSON(), nullable=True),
        sa.Column(
            "statut",
            sa.Enum(
                "RECU",
                "EN_COURS",
                "EVALUE",
                "ERREUR",
                "RETENU",
                "REJETE",
                name="candidaturestatut",
            ),
            nullable=False,
            server_default=sa.text("'RECU'"),
        ),
        sa.Column(
            "depose_le",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("evalue_le", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["projet_recrutement_id"], ["projets_recrutement.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "projet_recrutement_id",
            "email_candidat",
            name="uq_candidatures_projet_email_candidat",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("candidatures")
