"""merge heads

Revision ID: 6c138b22aaea
Revises: a8d4e2f6c1b9, c7d1f2a8b9c3
Create Date: 2026-07-15 11:56:04.307669

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c138b22aaea'
down_revision: Union[str, Sequence[str], None] = ('a8d4e2f6c1b9', 'c7d1f2a8b9c3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
