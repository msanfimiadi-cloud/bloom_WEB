"""add vk username to client profiles

Revision ID: 20260706_0023
Revises: 20260606_0022
Create Date: 2026-07-06 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260706_0023"
down_revision = "20260606_0022"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    columns = _column_names("client_profiles")
    if "vk_username" not in columns:
        op.add_column("client_profiles", sa.Column("vk_username", sa.String(length=255), nullable=True))


def downgrade() -> None:
    columns = _column_names("client_profiles")
    if "vk_username" in columns:
        op.drop_column("client_profiles", "vk_username")
