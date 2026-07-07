"""add partner contact and social link fields

Revision ID: 20260525_0014
Revises: 20260522_0013
Create Date: 2026-05-25 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260525_0014"
down_revision = "20260522_0013_merge_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("partners", sa.Column("instagram_url", sa.String(length=512), nullable=True))
    op.add_column("partners", sa.Column("vk_url", sa.String(length=512), nullable=True))
    op.add_column("partners", sa.Column("telegram_url", sa.String(length=512), nullable=True))
    op.add_column("partners", sa.Column("whatsapp_url", sa.String(length=512), nullable=True))
    op.add_column("partners", sa.Column("map_url", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("partners", "map_url")
    op.drop_column("partners", "whatsapp_url")
    op.drop_column("partners", "telegram_url")
    op.drop_column("partners", "vk_url")
    op.drop_column("partners", "instagram_url")
