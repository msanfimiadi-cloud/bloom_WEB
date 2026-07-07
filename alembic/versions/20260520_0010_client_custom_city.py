"""add client custom city

Revision ID: 20260520_0010
Revises: 20260519_0009
Create Date: 2026-05-20
"""

from alembic import op
import sqlalchemy as sa


revision = "20260520_0010"
down_revision = "20260519_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("client_profiles", sa.Column("custom_city", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("client_profiles", "custom_city")
