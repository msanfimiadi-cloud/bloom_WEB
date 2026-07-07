"""add browser login tokens

Revision ID: 20260703_0025
Revises: 20260630_0024
Create Date: 2026-07-03 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260703_0025"
down_revision = "20260630_0024"
branch_labels = None
depends_on = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _indexes(table: str) -> set[str]:
    return {i["name"] for i in sa.inspect(op.get_bind()).get_indexes(table)}


def upgrade() -> None:
    if "browser_login_tokens" not in _table_names():
        op.create_table(
            "browser_login_tokens",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(length=128), nullable=False),
            sa.Column("provider", sa.String(length=32), nullable=False),
            sa.Column("provider_user_id", sa.String(length=255), nullable=False),
            sa.Column("display_name", sa.String(length=255), nullable=True),
            sa.Column("username", sa.String(length=255), nullable=True),
            sa.Column("photo_url", sa.String(length=512), nullable=True),
            sa.Column("referral_code", sa.String(length=32), nullable=True),
            sa.Column("source", sa.String(length=64), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("created_by", sa.String(length=64), nullable=True),
            sa.Column("metadata_json", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token_hash", name="uq_browser_login_tokens_token_hash"),
        )
    indexes = _indexes("browser_login_tokens")
    for name, columns in {
        "ix_browser_login_tokens_token_hash": ["token_hash"],
        "ix_browser_login_tokens_provider": ["provider"],
        "ix_browser_login_tokens_provider_user_id": ["provider_user_id"],
        "ix_browser_login_tokens_referral_code": ["referral_code"],
        "ix_browser_login_tokens_source": ["source"],
        "ix_browser_login_tokens_expires_at": ["expires_at"],
        "ix_browser_login_tokens_used_at": ["used_at"],
        "ix_browser_login_tokens_revoked_at": ["revoked_at"],
    }.items():
        if name not in indexes:
            op.create_index(name, "browser_login_tokens", columns, unique=False)


def downgrade() -> None:
    if "browser_login_tokens" in _table_names():
        op.drop_table("browser_login_tokens")
