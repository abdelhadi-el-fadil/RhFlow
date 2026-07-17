"""add contenu_markdown to candidatures

Revision ID: c4a8e2d9f6b1
Revises: e4f7a1b9c2d3
Create Date: 2026-07-17 11:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4a8e2d9f6b1"
down_revision: Union[str, Sequence[str], None] = "e4f7a1b9c2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "candidatures",
        sa.Column("contenu_markdown", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("candidatures", "contenu_markdown")