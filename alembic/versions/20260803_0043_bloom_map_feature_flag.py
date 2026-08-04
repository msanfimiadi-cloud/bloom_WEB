"""add Bloom Map feature flag

Revision ID: 20260803_0043
Revises: 20260803_0042
"""

from alembic import op
import sqlalchemy as sa


revision = "20260803_0043"
down_revision = "20260803_0042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "landing_settings",
        sa.Column("bloom_map_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("landing_settings", "bloom_map_enabled")
