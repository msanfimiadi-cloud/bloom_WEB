"""add audit fields for manual petal awards

Revision ID: 20260722_0034
Revises: 20260721_0033
"""

from alembic import op
import sqlalchemy as sa


revision = "20260722_0034"
down_revision = "20260721_0033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bloom_petal_events",
        sa.Column("awarded_by_admin_id", sa.Integer(), nullable=True),
    )
    op.add_column("bloom_petal_events", sa.Column("note", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_bloom_petal_events_awarded_by_admin_id",
        "bloom_petal_events",
        "admin_users",
        ["awarded_by_admin_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_bloom_petal_events_awarded_by_admin_id",
        "bloom_petal_events",
        ["awarded_by_admin_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_bloom_petal_events_awarded_by_admin_id", table_name="bloom_petal_events")
    op.drop_constraint(
        "fk_bloom_petal_events_awarded_by_admin_id",
        "bloom_petal_events",
        type_="foreignkey",
    )
    op.drop_column("bloom_petal_events", "note")
    op.drop_column("bloom_petal_events", "awarded_by_admin_id")
