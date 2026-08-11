"""add partner online booking URL

Revision ID: 20260811_0044
Revises: 20260803_0043
"""

from alembic import op
import sqlalchemy as sa


revision = "20260811_0044"
down_revision = "20260803_0043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("partners", sa.Column("booking_url", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("partners", "booking_url")
