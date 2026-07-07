"""add offer photos gallery

Revision ID: 20260521_0011
Revises: 20260520_0010
Create Date: 2026-05-21 00:11:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260521_0011"
down_revision = "20260520_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "offer_photos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("offer_id", sa.Integer(), sa.ForeignKey("partner_offers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("alt_text", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_offer_photos_offer_id", "offer_photos", ["offer_id"])


def downgrade() -> None:
    op.drop_index("ix_offer_photos_offer_id", table_name="offer_photos")
    op.drop_table("offer_photos")
