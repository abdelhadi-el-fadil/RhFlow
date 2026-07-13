"""rename fiche description and drop status

Revision ID: e6a1b9c2d3f4
Revises: 1f3d9e7a2b6c
Create Date: 2026-07-13 14:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e6a1b9c2d3f4"
down_revision: Union[str, Sequence[str], None] = "1f3d9e7a2b6c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("fiches_de_poste")}

    if "description" in existing_columns and "main_activities" not in existing_columns:
        op.alter_column("fiches_de_poste", "description", new_column_name="main_activities")

    if "status" in existing_columns:
        op.drop_column("fiches_de_poste", "status")

    # The enum may still exist after dropping the column; remove it if present.
    op.execute("DROP TYPE IF EXISTS fichestatus")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("fiches_de_poste")}

    if "main_activities" in existing_columns and "description" not in existing_columns:
        op.alter_column("fiches_de_poste", "main_activities", new_column_name="description")

    if "status" not in existing_columns:
        fichestatus = sa.Enum("DRAFT", "VALIDATED", "ARCHIVED", name="fichestatus")
        fichestatus.create(bind, checkfirst=True)
        op.add_column(
            "fiches_de_poste",
            sa.Column(
                "status",
                fichestatus,
                nullable=False,
                server_default=sa.text("'DRAFT'"),
            ),
        )
