"""add client password setup tokens

Revision ID: 20260511_0007
Revises: 20260510_0006
Create Date: 2026-05-11 00:07:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260511_0007"
down_revision = "20260510_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_password_setup_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column(
            "purpose",
            sa.String(length=64),
            nullable=False,
            server_default="vk_onboarding_password_setup",
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("source", sa.String(length=64), nullable=True, server_default="vk"),
        sa.Column("vk_user_id", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("token_hash", name="uq_client_password_setup_tokens_token_hash"),
    )
    op.create_index("ix_client_password_setup_tokens_user_id", "client_password_setup_tokens", ["user_id"])
    op.create_index(
        "ix_client_password_setup_tokens_token_hash",
        "client_password_setup_tokens",
        ["token_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_client_password_setup_tokens_token_hash", table_name="client_password_setup_tokens")
    op.drop_index("ix_client_password_setup_tokens_user_id", table_name="client_password_setup_tokens")
    op.drop_table("client_password_setup_tokens")
