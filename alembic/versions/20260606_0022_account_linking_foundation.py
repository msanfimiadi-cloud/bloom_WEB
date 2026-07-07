"""add account linking foundation

Revision ID: 20260606_0022
Revises: 20260605_0021
Create Date: 2026-06-06 00:22:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260606_0022"
down_revision = "20260605_0021"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def _table_names() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return set(inspector.get_table_names())


def _index_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    user_columns = _column_names("users")
    if "phone_verified_at" not in user_columns:
        op.add_column("users", sa.Column("phone_verified_at", sa.DateTime(timezone=True), nullable=True))
    if "email_verified_at" not in user_columns:
        op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))

    if "client_identity_links" not in _table_names():
        op.create_table(
            "client_identity_links",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("client_profile_id", sa.Integer(), nullable=False),
            sa.Column("provider", sa.String(length=32), nullable=False),
            sa.Column("provider_user_id", sa.String(length=255), nullable=False),
            sa.Column("linked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["client_profile_id"], ["client_profiles.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("provider", "provider_user_id", name="uq_client_identity_links_provider_user"),
        )
    indexes = _index_names("client_identity_links")
    if "ix_client_identity_links_client_profile_id" not in indexes:
        op.create_index(
            "ix_client_identity_links_client_profile_id",
            "client_identity_links",
            ["client_profile_id"],
            unique=False,
        )


def downgrade() -> None:
    if "client_identity_links" in _table_names():
        indexes = _index_names("client_identity_links")
        if "ix_client_identity_links_client_profile_id" in indexes:
            op.drop_index("ix_client_identity_links_client_profile_id", table_name="client_identity_links")
        op.drop_table("client_identity_links")

    user_columns = _column_names("users")
    if "email_verified_at" in user_columns:
        op.drop_column("users", "email_verified_at")
    if "phone_verified_at" in user_columns:
        op.drop_column("users", "phone_verified_at")
