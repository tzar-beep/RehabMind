"""script practice: everyday phrases practised line by line

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-10-26 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "script_practice",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("script_id", sa.String(40), nullable=False),
        sa.Column("lines_said", sa.SmallInteger(), nullable=False),
        sa.Column("lines_total", sa.SmallInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_script_practice")),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            name=op.f("fk_script_practice_patient_id_patients"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(op.f("ix_script_practice_patient_id"), "script_practice", ["patient_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_script_practice_patient_id"), table_name="script_practice")
    op.drop_table("script_practice")
