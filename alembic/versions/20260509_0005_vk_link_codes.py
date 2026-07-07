"""add vk link codes

Revision ID: 20260509_0005
Revises: 20260509_0004
Create Date: 2026-05-09 00:05:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260509_0005"
down_revision = "20260509_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vk_link_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("client_profiles.id"), nullable=False),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("code", name="uq_vk_link_codes_code"),
    )
    op.create_index("ix_vk_link_codes_client_id", "vk_link_codes", ["client_id"])
    op.create_index("ix_vk_link_codes_code", "vk_link_codes", ["code"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_vk_link_codes_code", table_name="vk_link_codes")
    op.drop_index("ix_vk_link_codes_client_id", table_name="vk_link_codes")
    op.drop_table("vk_link_codes")
