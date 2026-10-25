"""therapy goals: clinician-set goals measured from practice data

Revision ID: 7d4b1c8e2a90
Revises: 6c3a9e2d5f17
Create Date: 2026-10-26 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7d4b1c8e2a90"
down_revision: str | Sequence[str] | None = "6c3a9e2d5f17"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "therapy_goals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("target", sa.SmallInteger(), nullable=False),
        sa.Column("category", sa.String(40)),
        sa.Column("due_on", sa.Date()),
        sa.Column("status", sa.String(12), nullable=False, server_default="active"),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("achieved_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_therapy_goals")),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            name=op.f("fk_therapy_goals_patient_id_patients"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f("fk_therapy_goals_created_by_users")
        ),
        sa.CheckConstraint(
            "kind IN ('name_words', 'practice_days')", name=op.f("ck_therapy_goals_kind")
        ),
        sa.CheckConstraint(
            "status IN ('active', 'achieved', 'ended')", name=op.f("ck_therapy_goals_status")
        ),
        sa.CheckConstraint("target BETWEEN 1 AND 200", name=op.f("ck_therapy_goals_target")),
        sa.CheckConstraint(
            "kind = 'name_words' OR target <= 7", name=op.f("ck_therapy_goals_days_in_week")
        ),
    )
    op.create_index(op.f("ix_therapy_goals_patient_id"), "therapy_goals", ["patient_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_therapy_goals_patient_id"), table_name="therapy_goals")
    op.drop_table("therapy_goals")
