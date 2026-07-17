"""convert candidature evaluation fields to json

Revision ID: e4f7a1b9c2d3
Revises: d9b3f1a2c4e5
Create Date: 2026-07-16 13:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e4f7a1b9c2d3"
down_revision: Union[str, Sequence[str], None] = "d9b3f1a2c4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        ALTER TABLE candidatures
        ALTER COLUMN points_forts TYPE jsonb
        USING CASE
            WHEN points_forts IS NULL THEN NULL
            WHEN pg_typeof(points_forts)::text IN ('json', 'jsonb') THEN
                CASE
                    WHEN jsonb_typeof(points_forts::jsonb) IN ('array', 'object') THEN points_forts::jsonb
                    WHEN btrim(points_forts::text, '"') = '' THEN '[]'::jsonb
                    ELSE to_jsonb(regexp_split_to_array(btrim(points_forts::text, '"'), E'\\n+'))
                END
            WHEN btrim(points_forts::text) = '' THEN '[]'::jsonb
            ELSE to_jsonb(regexp_split_to_array(points_forts::text, E'\\n+'))
        END
        """
    )
    op.execute(
        """
        ALTER TABLE candidatures
        ALTER COLUMN points_manquants TYPE jsonb
        USING CASE
            WHEN points_manquants IS NULL THEN NULL
            WHEN pg_typeof(points_manquants)::text IN ('json', 'jsonb') THEN
                CASE
                    WHEN jsonb_typeof(points_manquants::jsonb) IN ('array', 'object') THEN points_manquants::jsonb
                    WHEN btrim(points_manquants::text, '"') = '' THEN '[]'::jsonb
                    ELSE to_jsonb(regexp_split_to_array(btrim(points_manquants::text, '"'), E'\\n+'))
                END
            WHEN btrim(points_manquants::text) = '' THEN '[]'::jsonb
            ELSE to_jsonb(regexp_split_to_array(points_manquants::text, E'\\n+'))
        END
        """
    )
    op.execute(
        """
        ALTER TABLE candidatures
        ALTER COLUMN questions_entretien TYPE jsonb
        USING CASE
            WHEN questions_entretien IS NULL THEN NULL
            WHEN pg_typeof(questions_entretien)::text IN ('json', 'jsonb') THEN
                CASE
                    WHEN jsonb_typeof(questions_entretien::jsonb) IN ('array', 'object') THEN questions_entretien::jsonb
                    WHEN btrim(questions_entretien::text, '"') = '' THEN '[]'::jsonb
                    ELSE to_jsonb(regexp_split_to_array(btrim(questions_entretien::text, '"'), E'\\n+'))
                END
            WHEN btrim(questions_entretien::text) = '' THEN '[]'::jsonb
            ELSE to_jsonb(regexp_split_to_array(questions_entretien::text, E'\\n+'))
        END
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        """
        ALTER TABLE candidatures
        ALTER COLUMN points_forts TYPE text
        USING CASE
            WHEN points_forts IS NULL THEN NULL
            ELSE array_to_string(ARRAY(SELECT jsonb_array_elements_text(points_forts)), E'\\n')
        END
        """
    )
    op.execute(
        """
        ALTER TABLE candidatures
        ALTER COLUMN points_manquants TYPE text
        USING CASE
            WHEN points_manquants IS NULL THEN NULL
            ELSE array_to_string(ARRAY(SELECT jsonb_array_elements_text(points_manquants)), E'\\n')
        END
        """
    )
    op.execute(
        """
        ALTER TABLE candidatures
        ALTER COLUMN questions_entretien TYPE text
        USING CASE
            WHEN questions_entretien IS NULL THEN NULL
            ELSE array_to_string(ARRAY(SELECT jsonb_array_elements_text(questions_entretien)), E'\\n')
        END
        """
    )
