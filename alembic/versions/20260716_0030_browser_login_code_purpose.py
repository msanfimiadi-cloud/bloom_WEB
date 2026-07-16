"""add browser login code purpose

Revision ID: 20260716_0030
Revises: 20260714_0029
Create Date: 2026-07-16 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260716_0030"
down_revision = "20260714_0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("browser_login_codes", sa.Column("purpose", sa.String(length=32), nullable=False, server_default="login"))
    op.create_index("ix_browser_login_codes_purpose", "browser_login_codes", ["purpose"])


def downgrade() -> None:
    op.drop_index("ix_browser_login_codes_purpose", table_name="browser_login_codes")
    op.drop_column("browser_login_codes", "purpose")
