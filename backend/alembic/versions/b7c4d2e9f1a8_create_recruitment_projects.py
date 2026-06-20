"""create recruitment projects

Revision ID: b7c4d2e9f1a8
Revises: 6f1dc2f355e2
Create Date: 2026-06-19 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7c4d2e9f1a8"
down_revision: Union[str, Sequence[str], None] = "6f1dc2f355e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "projets_recrutement",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("expected_end_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "ACTIVE", "CLOSED", name="projetstatus"),
            server_default=sa.text("'DRAFT'"),
            nullable=False,
        ),
        sa.Column("manager_id", sa.Integer(), nullable=False),
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
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "besoins_recrutement",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("positions_count", sa.Integer(), nullable=True),
        sa.Column("desired_date", sa.Date(), nullable=True),
        sa.Column("justification", sa.String(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "SUBMITTED", "APPROVED", "REJECTED", name="besoinstatus"),
            server_default=sa.text("'DRAFT'"),
            nullable=False,
        ),
        sa.Column("rejection_reason", sa.String(), nullable=True),
        sa.Column("fiche_de_poste_id", sa.Integer(), nullable=True),
        sa.Column("submitted_by_id", sa.Integer(), nullable=True),
        sa.Column("processed_by_id", sa.Integer(), nullable=True),
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
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["processed_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["submitted_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.add_column(
        "besoins_recrutement",
        sa.Column("projet_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_besoins_recrutement_projet_id_projets_recrutement",
        "besoins_recrutement",
        "projets_recrutement",
        ["projet_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_besoins_recrutement_projet_id_projets_recrutement",
        "besoins_recrutement",
        type_="foreignkey",
    )
    op.drop_column("besoins_recrutement", "projet_id")
    op.drop_table("besoins_recrutement")
    op.drop_table("projets_recrutement")
    sa.Enum(name="besoinstatus").drop(op.get_bind())
    sa.Enum(name="projetstatus").drop(op.get_bind())