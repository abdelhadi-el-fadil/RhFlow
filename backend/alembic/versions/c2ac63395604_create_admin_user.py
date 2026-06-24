"""create ADMIN user

Revision ID: c2ac63395604
Revises: f2b8c9d1a7e4
Create Date: 2026-06-24 16:15:21.641178

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext


# revision identifiers, used by Alembic.
revision: str = 'c2ac63395604'
down_revision: Union[str, Sequence[str], None] = 'f2b8c9d1a7e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade() -> None:
    users_table = sa.table(
        "users",
        sa.column("email", sa.String),
        sa.column("full_name", sa.String),
        sa.column("hashed_password", sa.String),
        sa.column("role", sa.String),
        sa.column("enabled", sa.Boolean),
        sa.column("gsm", sa.String),
    )

    op.bulk_insert(users_table, [
        {
            "email": "admin@example.com",
            "full_name": "System Admin",
            "hashed_password": pwd_context.hash("Admin123"),
            "role": "ADMIN",
            "enabled": True,
            "gsm": None,
        }
    ])


def downgrade() -> None:
    op.execute("DELETE FROM users WHERE email = 'admin@example.com'")