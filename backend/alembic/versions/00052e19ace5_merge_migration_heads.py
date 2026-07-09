"""Merge migration heads

Revision ID: 00052e19ace5
Revises: 3d6f2d1c4a5b, c2ac63395604
Create Date: 2026-07-08 17:00:40.940467

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00052e19ace5'
down_revision: Union[str, Sequence[str], None] = ('3d6f2d1c4a5b', 'c2ac63395604')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
