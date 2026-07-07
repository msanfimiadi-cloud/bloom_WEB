"""add partner gallery photos

Revision ID: 20260514_0008
Revises: 20260511_0007
Create Date: 2026-05-14 00:08:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260514_0008"
down_revision = "20260511_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "partner_photos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("partner_id", sa.Integer(), sa.ForeignKey("partners.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("alt_text", sa.String(length=255), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_partner_photos_partner_id", "partner_photos", ["partner_id"])


def downgrade() -> None:
    op.drop_index("ix_partner_photos_partner_id", table_name="partner_photos")
    op.drop_table("partner_photos")
