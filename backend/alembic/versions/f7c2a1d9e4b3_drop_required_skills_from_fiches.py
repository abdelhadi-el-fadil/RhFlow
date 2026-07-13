"""drop required_skills from fiches

Revision ID: f7c2a1d9e4b3
Revises: e6a1b9c2d3f4
Create Date: 2026-07-13 17:20:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f7c2a1d9e4b3"
down_revision: Union[str, Sequence[str], None] = "e6a1b9c2d3f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("fiches_de_poste")}

    if "required_skills" in existing_columns:
        op.drop_column("fiches_de_poste", "required_skills")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("fiches_de_poste")}

    if "required_skills" not in existing_columns:
        op.add_column(
            "fiches_de_poste",
            sa.Column("required_skills", sa.Text(), nullable=False, server_default=""),
        )
