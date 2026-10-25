"""encouragements: short notes from carers to the patient

Revision ID: a1b2c3d4e5f6
Revises: 9f6d3e0a4c52
Create Date: 2026-10-26 13:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "9f6d3e0a4c52"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "encouragements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.String(200), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("seen_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_encouragements")),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            name=op.f("fk_encouragements_patient_id_patients"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
            name=op.f("fk_encouragements_author_id_users"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(op.f("ix_encouragements_patient_id"), "encouragements", ["patient_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_encouragements_patient_id"), table_name="encouragements")
    op.drop_table("encouragements")
