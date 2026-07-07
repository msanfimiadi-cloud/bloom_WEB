"""admin users auth mvp

Revision ID: 20260508_0003
Revises: 20260508_0002
Create Date: 2026-05-08 00:03:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260508_0003"
down_revision = "20260508_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="admin"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("email", name="uq_admin_users_email"),
    )
    op.create_index("ix_admin_users_email", "admin_users", ["email"])


def downgrade() -> None:
    op.drop_index("ix_admin_users_email", table_name="admin_users")
    op.drop_table("admin_users")
