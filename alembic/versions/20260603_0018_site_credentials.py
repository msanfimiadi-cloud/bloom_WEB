"""add generated site credentials to users

Revision ID: 20260603_0018
Revises: 20260602_0017
Create Date: 2026-06-03 00:18:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260603_0018"
down_revision = "20260602_0017"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def _index_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    columns = _column_names("users")
    if "site_login" not in columns:
        op.add_column("users", sa.Column("site_login", sa.String(length=255), nullable=True))
    if "encrypted_site_password" not in columns:
        op.add_column("users", sa.Column("encrypted_site_password", sa.String(length=2048), nullable=True))
    if "site_credentials_created_at" not in columns:
        op.add_column("users", sa.Column("site_credentials_created_at", sa.DateTime(timezone=True), nullable=True))

    if "ix_users_site_login" not in _index_names("users"):
        op.create_index("ix_users_site_login", "users", ["site_login"], unique=True)


def downgrade() -> None:
    if "ix_users_site_login" in _index_names("users"):
        op.drop_index("ix_users_site_login", table_name="users")

    columns = _column_names("users")
    if "site_credentials_created_at" in columns:
        op.drop_column("users", "site_credentials_created_at")
    if "encrypted_site_password" in columns:
        op.drop_column("users", "encrypted_site_password")
    if "site_login" in columns:
        op.drop_column("users", "site_login")
