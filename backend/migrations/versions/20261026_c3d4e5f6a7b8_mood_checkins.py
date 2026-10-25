"""mood check-ins: one tap a day on the patient's home

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-10-26 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "mood_checkins",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("mood", sa.String(8), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_mood_checkins")),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            name=op.f("fk_mood_checkins_patient_id_patients"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("patient_id", "day", name=op.f("uq_mood_checkins_patient_id")),
        sa.CheckConstraint("mood IN ('good', 'okay', 'low')", name=op.f("ck_mood_checkins_mood")),
    )
    op.create_index(op.f("ix_mood_checkins_patient_id"), "mood_checkins", ["patient_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_mood_checkins_patient_id"), table_name="mood_checkins")
    op.drop_table("mood_checkins")
