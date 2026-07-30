"""add user giveaway exclusion flag

Revision ID: 20260730_0040
Revises: 20260728_0039
"""

from alembic import op
import sqlalchemy as sa


revision = "20260730_0040"
down_revision = "20260728_0039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "exclude_from_giveaways",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "exclude_from_giveaways")
