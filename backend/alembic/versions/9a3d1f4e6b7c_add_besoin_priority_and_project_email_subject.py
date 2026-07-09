"""add besoin priority and project email subject

Revision ID: 9a3d1f4e6b7c
Revises: 7b82c3a4d9ef
Create Date: 2026-07-09 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a3d1f4e6b7c"
down_revision: Union[str, Sequence[str], None] = "7b82c3a4d9ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


besoin_priority_enum = sa.Enum("HAUTE", "NORMALE", "BASSE", name="besoinpriority")


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    besoin_priority_enum.create(bind, checkfirst=True)

    op.add_column(
        "besoins_recrutement",
        sa.Column(
            "priority",
            besoin_priority_enum,
            nullable=False,
            server_default=sa.text("'NORMALE'"),
        ),
    )
    op.add_column(
        "projets_recrutement",
        sa.Column("email_subject", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("projets_recrutement", "email_subject")
    op.drop_column("besoins_recrutement", "priority")

    bind = op.get_bind()
    besoin_priority_enum.drop(bind, checkfirst=True)
