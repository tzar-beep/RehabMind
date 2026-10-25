"""speech confirmation: a recognised match waits for the patient to confirm it

Revision ID: 6c3a9e2d5f17
Revises: 4d7e1f0a9b21
Create Date: 2026-10-25 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6c3a9e2d5f17"
down_revision: str | Sequence[str] | None = "4d7e1f0a9b21"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """The transcript is held only until the patient confirms or rejects it."""
    op.add_column("audio_assets", sa.Column("transcript", sa.String(200)))
    op.add_column("audio_assets", sa.Column("stt", postgresql.JSONB()))


def downgrade() -> None:
    op.drop_column("audio_assets", "stt")
    op.drop_column("audio_assets", "transcript")
