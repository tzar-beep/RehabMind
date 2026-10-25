"""carers: a family member or carer linked to a patient

Revision ID: 8e5c2d9f3b41
Revises: 7d4b1c8e2a90
Create Date: 2026-10-26 11:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8e5c2d9f3b41"
down_revision: str | Sequence[str] | None = "7d4b1c8e2a90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'carer'")
    op.create_table(
        "patient_carers",
        sa.Column("patient_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("relationship", sa.String(40), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("patient_id", "user_id", name=op.f("pk_patient_carers")),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            name=op.f("fk_patient_carers_patient_id_patients"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_patient_carers_user_id_users"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(op.f("ix_patient_carers_user_id"), "patient_carers", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_patient_carers_user_id"), table_name="patient_carers")
    op.drop_table("patient_carers")
    # Postgres cannot drop an enum value; 'carer' stays in user_role (unused).
