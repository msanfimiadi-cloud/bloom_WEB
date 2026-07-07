"""add browser login codes

Revision ID: 20260706_0026
Revises: 20260703_0025
Create Date: 2026-07-06 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260706_0026"
down_revision = "20260703_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "browser_login_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column("login_code", sa.String(length=16), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("photo_url", sa.String(length=512), nullable=True),
        sa.Column("referral_code", sa.String(length=32), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=True),
        sa.Column("attempts_count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("login_code", name="uq_browser_login_codes_login_code"),
    )
    for col in ["provider", "provider_user_id", "login_code", "referral_code", "source", "expires_at", "used_at"]:
        op.create_index(f"ix_browser_login_codes_{col}", "browser_login_codes", [col])


def downgrade() -> None:
    op.drop_table("browser_login_codes")
