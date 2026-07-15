"""drop offres and add offre to recruitment projects

Revision ID: c7d1f2a8b9c3
Revises: 00052e19ace5
Create Date: 2026-07-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7d1f2a8b9c3"
down_revision: Union[str, Sequence[str], None] = "00052e19ace5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projets_recrutement", sa.Column("offre", sa.Text(), nullable=True))
    op.drop_table("offres")
    sa.Enum(name="offrestatus").drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    op.create_table(
        "offres",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("requirements", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "PUBLISHED", "CLOSED", name="offrestatus"),
            server_default=sa.text("'DRAFT'"),
            nullable=False,
        ),
        sa.Column("besoin_id", sa.Integer(), nullable=False),
        sa.Column("published_by_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["besoin_id"], ["besoins_recrutement.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["published_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.drop_column("projets_recrutement", "offre")
