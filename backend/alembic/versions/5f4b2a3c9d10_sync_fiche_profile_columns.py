"""sync fiche profile columns

Revision ID: 5f4b2a3c9d10
Revises: 00052e19ace5
Create Date: 2026-07-08 17:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "5f4b2a3c9d10"
down_revision: Union[str, Sequence[str], None] = "00052e19ace5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("fiches_de_poste")}

    rename_map = {
        "domaine_formation": "formation_domain",
        "niveau_etudes": "education_level",
        "competences_techniques": "technical_skills",
        "competences_manageriales": "managerial_skills",
    }

    for old_name, new_name in rename_map.items():
        if old_name in existing_columns and new_name not in existing_columns:
            op.alter_column("fiches_de_poste", old_name, new_column_name=new_name)

    if "annees_experience" in existing_columns:
        op.drop_column("fiches_de_poste", "annees_experience")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("fiches_de_poste")}

    reverse_map = {
        "formation_domain": "domaine_formation",
        "education_level": "niveau_etudes",
        "technical_skills": "competences_techniques",
        "managerial_skills": "competences_manageriales",
    }

    for old_name, new_name in reverse_map.items():
        if old_name in existing_columns and new_name not in existing_columns:
            op.alter_column("fiches_de_poste", old_name, new_column_name=new_name)
