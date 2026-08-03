"""add partner coordinates for Bloom Map

Revision ID: 20260803_0042
Revises: 20260731_0041
"""

from alembic import op
import sqlalchemy as sa


revision = "20260803_0042"
down_revision = "20260731_0041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("partners", sa.Column("latitude", sa.Numeric(9, 6), nullable=True))
    op.add_column("partners", sa.Column("longitude", sa.Numeric(9, 6), nullable=True))


def downgrade() -> None:
    op.drop_column("partners", "longitude")
    op.drop_column("partners", "latitude")
