"""personal words: a patient's own photos and words

Revision ID: 9f6d3e0a4c52
Revises: 8e5c2d9f3b41
Create Date: 2026-10-26 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9f6d3e0a4c52"
down_revision: str | Sequence[str] | None = "8e5c2d9f3b41"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("stimuli", sa.Column("owner_patient_id", sa.Uuid()))
    op.add_column("stimuli", sa.Column("added_by", sa.Uuid()))
    op.create_foreign_key(
        op.f("fk_stimuli_owner_patient_id_patients"),
        "stimuli",
        "patients",
        ["owner_patient_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_stimuli_added_by_users"), "stimuli", "users", ["added_by"], ["id"]
    )
    op.create_index(op.f("ix_stimuli_owner_patient_id"), "stimuli", ["owner_patient_id"])
    op.create_table(
        "personal_photos",
        sa.Column("stimulus_id", sa.Uuid(), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("stimulus_id", name=op.f("pk_personal_photos")),
        sa.ForeignKeyConstraint(
            ["stimulus_id"],
            ["stimuli.id"],
            name=op.f("fk_personal_photos_stimulus_id_stimuli"),
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    op.drop_table("personal_photos")
    op.drop_index(op.f("ix_stimuli_owner_patient_id"), table_name="stimuli")
    op.drop_constraint(op.f("fk_stimuli_added_by_users"), "stimuli", type_="foreignkey")
    op.drop_constraint(op.f("fk_stimuli_owner_patient_id_patients"), "stimuli", type_="foreignkey")
    op.drop_column("stimuli", "added_by")
    op.drop_column("stimuli", "owner_patient_id")
