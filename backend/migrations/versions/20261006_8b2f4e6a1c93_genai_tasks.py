"""genai tasks: summaries without a session, token usage

Revision ID: 8b2f4e6a1c93
Revises: 5e1a9c3b7d20
Create Date: 2026-10-06 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8b2f4e6a1c93"
down_revision: str | Sequence[str] | None = "5e1a9c3b7d20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Progress summaries are patient-level AI calls with no practice session.
    op.alter_column("ai_generations", "session_id", existing_type=sa.Uuid(), nullable=True)
    op.add_column(
        "ai_generations",
        sa.Column("usage", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("ix_ai_generations_exercise_task", "ai_generations", ["exercise_id", "task"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_ai_generations_exercise_task", table_name="ai_generations")
    op.drop_column("ai_generations", "usage")
    op.execute("DELETE FROM ai_generations WHERE session_id IS NULL")
    op.alter_column("ai_generations", "session_id", existing_type=sa.Uuid(), nullable=False)
