"""add privilege session tokens

Revision ID: 20260602_0016
Revises: 20260601_0015
Create Date: 2026-06-02 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260602_0016"
down_revision = "20260601_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("privilege_verification_sessions", sa.Column("token", sa.String(length=128), nullable=True))
    op.create_index(
        "ix_privilege_verification_sessions_token",
        "privilege_verification_sessions",
        ["token"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_privilege_verification_sessions_token", table_name="privilege_verification_sessions")
    op.drop_column("privilege_verification_sessions", "token")
