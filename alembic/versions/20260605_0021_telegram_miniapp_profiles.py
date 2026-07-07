"""add telegram miniapp profile fields

Revision ID: 20260605_0021
Revises: 20260604_0020
Create Date: 2026-06-05 00:21:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260605_0021"
down_revision = "20260604_0020"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def _index_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    columns = _column_names("client_profiles")
    if "telegram_user_id" not in columns:
        op.add_column("client_profiles", sa.Column("telegram_user_id", sa.String(length=255), nullable=True))
    if "telegram_username" not in columns:
        op.add_column("client_profiles", sa.Column("telegram_username", sa.String(length=255), nullable=True))
    if "telegram_first_name" not in columns:
        op.add_column("client_profiles", sa.Column("telegram_first_name", sa.String(length=255), nullable=True))
    if "telegram_last_name" not in columns:
        op.add_column("client_profiles", sa.Column("telegram_last_name", sa.String(length=255), nullable=True))
    if "telegram_photo_url" not in columns:
        op.add_column("client_profiles", sa.Column("telegram_photo_url", sa.String(length=512), nullable=True))

    indexes = _index_names("client_profiles")
    if "ix_client_profiles_telegram_user_id" not in indexes:
        op.create_index(
            "ix_client_profiles_telegram_user_id",
            "client_profiles",
            ["telegram_user_id"],
            unique=True,
        )


def downgrade() -> None:
    indexes = _index_names("client_profiles")
    if "ix_client_profiles_telegram_user_id" in indexes:
        op.drop_index("ix_client_profiles_telegram_user_id", table_name="client_profiles")

    columns = _column_names("client_profiles")
    for column_name in (
        "telegram_photo_url",
        "telegram_last_name",
        "telegram_first_name",
        "telegram_username",
        "telegram_user_id",
    ):
        if column_name in columns:
            op.drop_column("client_profiles", column_name)
