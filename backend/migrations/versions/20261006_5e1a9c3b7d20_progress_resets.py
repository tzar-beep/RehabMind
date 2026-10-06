"""progress resets

Revision ID: 5e1a9c3b7d20
Revises: 103dc834422a
Create Date: 2026-10-06 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5e1a9c3b7d20"
down_revision: str | Sequence[str] | None = "103dc834422a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "progress_resets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("reset_by", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("previous_levels", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reset_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_progress_resets_patient_created", "progress_resets", ["patient_id", "created_at"]
    )
    # A reset is a clinical record: the runtime role may add resets but never alter them.
    op.execute("REVOKE UPDATE, DELETE, TRUNCATE ON progress_resets FROM rehabmind_app")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_progress_resets_patient_created", table_name="progress_resets")
    op.drop_table("progress_resets")
