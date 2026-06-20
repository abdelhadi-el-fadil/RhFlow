"""create fiches de poste

Revision ID: c1f8d3a4b7e1
Revises: b7c4d2e9f1a8
Create Date: 2026-06-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1f8d3a4b7e1"
down_revision: Union[str, Sequence[str], None] = "b7c4d2e9f1a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fiches_de_poste",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("missions", sa.Text(), nullable=False),
        sa.Column("required_skills", sa.Text(), nullable=False),
        sa.Column("experience_level", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "VALIDATED", "ARCHIVED", name="fichestatus"),
            server_default=sa.text("'DRAFT'"),
            nullable=False,
        ),
        sa.Column("direction_id", sa.Integer(), nullable=False),
        sa.Column("validated_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["direction_id"], ["directions.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["validated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("fiches_de_poste")
    sa.Enum(name="fichestatus").drop(op.get_bind())
