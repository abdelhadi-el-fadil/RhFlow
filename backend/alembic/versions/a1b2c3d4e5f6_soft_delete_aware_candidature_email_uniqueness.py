"""soft delete aware candidature email uniqueness

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-07-21 15:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        "uq_candidatures_projet_email_candidat",
        "candidatures",
        type_="unique",
    )
    op.create_index(
        "uq_candidatures_projet_email_candidat_active",
        "candidatures",
        ["projet_recrutement_id", "email_candidat"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false AND email_candidat IS NOT NULL"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "uq_candidatures_projet_email_candidat_active",
        table_name="candidatures",
    )
    op.create_unique_constraint(
        "uq_candidatures_projet_email_candidat",
        "candidatures",
        ["projet_recrutement_id", "email_candidat"],
    )
