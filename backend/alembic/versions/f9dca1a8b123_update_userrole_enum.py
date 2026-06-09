"""update userrole enum values

Revision ID: f9dca1a8b123
Revises: 18f8ff1385b8
Create Date: 2026-06-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f9dca1a8b123'
down_revision = '8a996f8eaeef'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE userrole RENAME TO userrole_old")
    op.execute("CREATE TYPE userrole AS ENUM ('ADMIN', 'DRH', 'DIRECTEUR', 'DG')")
    op.execute(
        "ALTER TABLE users ALTER COLUMN role TYPE userrole USING CASE "
        "role::text WHEN 'admin' THEN 'ADMIN' WHEN 'user' THEN 'DRH' ELSE role::text END::userrole"
    )
    op.execute("DROP TYPE userrole_old")


def downgrade() -> None:
    op.execute("CREATE TYPE userrole_old AS ENUM ('admin', 'user')")
    op.execute(
        "ALTER TABLE users ALTER COLUMN role TYPE userrole_old USING CASE "
        "role::text WHEN 'ADMIN' THEN 'admin' WHEN 'DRH' THEN 'user' "
        "WHEN 'DIRECTEUR' THEN 'user' WHEN 'DG' THEN 'user' ELSE role::text END::userrole_old"
    )
    op.execute("DROP TYPE userrole")
    op.execute("ALTER TYPE userrole_old RENAME TO userrole")
