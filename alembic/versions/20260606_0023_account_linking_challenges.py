"""add account linking challenges

Revision ID: 20260606_0023
Revises: 20260606_0022
Create Date: 2026-06-06 10:30:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260606_0023"
down_revision = "20260606_0022"
branch_labels = None
depends_on = None


def _table_names() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return set(inspector.get_table_names())


def _index_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if "account_linking_challenges" not in _table_names():
        op.create_table(
            "account_linking_challenges",
            sa.Column("id", sa.String(length=64), nullable=False),
            sa.Column("current_client_profile_id", sa.Integer(), nullable=False),
            sa.Column("target_client_profile_id", sa.Integer(), nullable=False),
            sa.Column("identifier_type", sa.String(length=16), nullable=False),
            sa.Column("identifier_hash", sa.String(length=128), nullable=False),
            sa.Column("code_hash", sa.String(length=128), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("attempts_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["current_client_profile_id"], ["client_profiles.id"]),
            sa.ForeignKeyConstraint(["target_client_profile_id"], ["client_profiles.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    indexes = _index_names("account_linking_challenges")
    for name, columns in {
        "ix_account_linking_challenges_current_client_profile_id": ["current_client_profile_id"],
        "ix_account_linking_challenges_target_client_profile_id": ["target_client_profile_id"],
        "ix_account_linking_challenges_identifier_hash": ["identifier_hash"],
        "ix_account_linking_challenges_expires_at": ["expires_at"],
    }.items():
        if name not in indexes:
            op.create_index(name, "account_linking_challenges", columns, unique=False)


def downgrade() -> None:
    if "account_linking_challenges" in _table_names():
        indexes = _index_names("account_linking_challenges")
        for name in (
            "ix_account_linking_challenges_expires_at",
            "ix_account_linking_challenges_identifier_hash",
            "ix_account_linking_challenges_target_client_profile_id",
            "ix_account_linking_challenges_current_client_profile_id",
        ):
            if name in indexes:
                op.drop_index(name, table_name="account_linking_challenges")
        op.drop_table("account_linking_challenges")
