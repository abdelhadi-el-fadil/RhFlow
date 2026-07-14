"""cleanup recruitment models and workflows

Revision ID: a8d4e2f6c1b9
Revises: f7c2a1d9e4b3
Create Date: 2026-07-13 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a8d4e2f6c1b9"
down_revision: Union[str, Sequence[str], None] = "f7c2a1d9e4b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _migrate_besoin_status_to_new_enum() -> None:
    op.execute("ALTER TABLE besoins_recrutement ALTER COLUMN status DROP DEFAULT")
    op.execute("UPDATE besoins_recrutement SET status = 'SUBMITTED' WHERE status = 'DRAFT'")
    op.execute("ALTER TYPE besoinstatus RENAME TO besoinstatus_old")
    op.execute("CREATE TYPE besoinstatus AS ENUM ('SUBMITTED', 'APPROVED', 'REJECTED')")
    op.execute(
        """
        ALTER TABLE besoins_recrutement
        ALTER COLUMN status TYPE besoinstatus
        USING status::text::besoinstatus
        """
    )
    op.execute("DROP TYPE besoinstatus_old")


def _migrate_project_status_to_new_enum() -> None:
    op.execute("ALTER TABLE projets_recrutement ALTER COLUMN status DROP DEFAULT")
    op.execute("UPDATE projets_recrutement SET status = 'ACTIVE' WHERE status = 'DRAFT'")
    op.execute("ALTER TYPE projetstatus RENAME TO projetstatus_old")
    op.execute("CREATE TYPE projetstatus AS ENUM ('ACTIVE', 'CLOSED')")
    op.execute(
        """
        ALTER TABLE projets_recrutement
        ALTER COLUMN status TYPE projetstatus
        USING status::text::projetstatus
        """
    )
    op.execute("DROP TYPE projetstatus_old")


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        UPDATE projets_recrutement AS p
        SET besoin_recrutement_id = b.id
        FROM besoins_recrutement AS b
        WHERE b.projet_id = p.id
          AND p.besoin_recrutement_id IS NULL
        """
    )

    op.add_column(
        "besoins_recrutement",
        sa.Column("lieu_affectation", sa.String(length=255), nullable=True),
    )
    op.execute(
        """
        UPDATE besoins_recrutement
        SET lieu_affectation = COALESCE(description, '')
        """
    )
    op.alter_column("besoins_recrutement", "lieu_affectation", nullable=False)

    op.drop_constraint(
        "fk_besoins_recrutement_projet_id_projets_recrutement",
        "besoins_recrutement",
        type_="foreignkey",
    )
    op.drop_column("besoins_recrutement", "title")
    op.drop_column("besoins_recrutement", "description")
    op.drop_column("besoins_recrutement", "rejection_reason")
    op.drop_column("besoins_recrutement", "projet_id")

    _migrate_besoin_status_to_new_enum()
    op.alter_column(
        "besoins_recrutement",
        "status",
        server_default=sa.text("'SUBMITTED'"),
    )

    op.add_column(
        "projets_recrutement",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.drop_constraint("fk_proj_fiche_id", "projets_recrutement", type_="foreignkey")
    op.drop_column("projets_recrutement", "title")
    op.drop_column("projets_recrutement", "description")
    op.drop_column("projets_recrutement", "start_date")
    op.drop_column("projets_recrutement", "expected_end_date")
    op.drop_column("projets_recrutement", "fiche_de_poste_id")
    op.drop_column("projets_recrutement", "nombre_postes")

    _migrate_project_status_to_new_enum()
    op.alter_column(
        "projets_recrutement",
        "status",
        server_default=sa.text("'ACTIVE'"),
    )

    op.execute(
        """
        UPDATE projets_recrutement
        SET is_deleted = true,
            deleted_at = now()
        WHERE besoin_recrutement_id IS NULL
        """
    )
    op.execute(
        """
        DELETE FROM projets_recrutement
        WHERE besoin_recrutement_id IS NULL
        """
    )
    op.alter_column("projets_recrutement", "besoin_recrutement_id", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("projets_recrutement", "besoin_recrutement_id", nullable=True)

    op.execute("ALTER TABLE projets_recrutement ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TYPE projetstatus RENAME TO projetstatus_new")
    op.execute("CREATE TYPE projetstatus AS ENUM ('DRAFT', 'ACTIVE', 'CLOSED')")
    op.execute(
        """
        ALTER TABLE projets_recrutement
        ALTER COLUMN status TYPE projetstatus
        USING status::text::projetstatus
        """
    )
    op.execute("DROP TYPE projetstatus_new")

    op.add_column("projets_recrutement", sa.Column("nombre_postes", sa.Integer(), nullable=True))
    op.add_column("projets_recrutement", sa.Column("fiche_de_poste_id", sa.Integer(), nullable=True))
    op.add_column("projets_recrutement", sa.Column("expected_end_date", sa.Date(), nullable=True))
    op.add_column("projets_recrutement", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column("projets_recrutement", sa.Column("description", sa.String(), nullable=True))
    op.add_column("projets_recrutement", sa.Column("title", sa.String(length=150), nullable=False, server_default="Projet"))
    op.create_foreign_key(
        "fk_proj_fiche_id",
        "projets_recrutement",
        "fiches_de_poste",
        ["fiche_de_poste_id"],
        ["id"],
    )
    op.drop_column("projets_recrutement", "archived_at")

    op.execute("ALTER TABLE besoins_recrutement ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TYPE besoinstatus RENAME TO besoinstatus_new")
    op.execute("CREATE TYPE besoinstatus AS ENUM ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED')")
    op.execute(
        """
        ALTER TABLE besoins_recrutement
        ALTER COLUMN status TYPE besoinstatus
        USING status::text::besoinstatus
        """
    )
    op.execute("DROP TYPE besoinstatus_new")

    op.add_column("besoins_recrutement", sa.Column("projet_id", sa.Integer(), nullable=True))
    op.add_column("besoins_recrutement", sa.Column("rejection_reason", sa.String(), nullable=True))
    op.add_column("besoins_recrutement", sa.Column("description", sa.String(), nullable=True))
    op.add_column("besoins_recrutement", sa.Column("title", sa.String(length=150), nullable=False, server_default="Besoin"))
    op.create_foreign_key(
        "fk_besoins_recrutement_projet_id_projets_recrutement",
        "besoins_recrutement",
        "projets_recrutement",
        ["projet_id"],
        ["id"],
    )
    op.drop_column("besoins_recrutement", "lieu_affectation")

    op.alter_column("besoins_recrutement", "status", server_default=sa.text("'DRAFT'"))
    op.alter_column("projets_recrutement", "status", server_default=sa.text("'DRAFT'"))
