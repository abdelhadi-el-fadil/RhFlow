"""add user signature columns

Revision ID: 1f3d9e7a2b6c
Revises: 9a3d1f4e6b7c
Create Date: 2026-07-09 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1f3d9e7a2b6c"
down_revision: Union[str, Sequence[str], None] = "9a3d1f4e6b7c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("signature_key", sa.String(length=500), nullable=True))
    op.add_column(
        "users",
        sa.Column("signature_content_type", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "signature_content_type")
    op.drop_column("users", "signature_key")
