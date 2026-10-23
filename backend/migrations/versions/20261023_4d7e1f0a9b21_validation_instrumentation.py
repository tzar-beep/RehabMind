"""validation instrumentation: progression mode, session difficulty rating

Revision ID: 4d7e1f0a9b21
Revises: 8b2f4e6a1c93
Create Date: 2026-10-23 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4d7e1f0a9b21"
down_revision: str | Sequence[str] | None = "8b2f4e6a1c93"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Existing versions keep the step rule they were written with."""
    op.add_column(
        "clinical_constraint_sets",
        sa.Column("progression_mode", sa.String(16), nullable=False, server_default="step"),
    )
    op.create_check_constraint(
        op.f("ck_clinical_constraint_sets_progression_mode"),
        "clinical_constraint_sets",
        "progression_mode IN ('step', 'ability')",
    )
    op.add_column("practice_sessions", sa.Column("difficulty_rating", sa.String(16)))
    op.create_check_constraint(
        op.f("ck_practice_sessions_difficulty_rating"),
        "practice_sessions",
        "difficulty_rating IN ('too_easy', 'just_right', 'too_hard')",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_practice_sessions_difficulty_rating"), "practice_sessions", type_="check"
    )
    op.drop_column("practice_sessions", "difficulty_rating")
    op.drop_constraint(
        op.f("ck_clinical_constraint_sets_progression_mode"),
        "clinical_constraint_sets",
        type_="check",
    )
    op.drop_column("clinical_constraint_sets", "progression_mode")
