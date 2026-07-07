"""add trial subscription activation fields

Revision ID: 20260604_0019
Revises: 20260603_0018
Create Date: 2026-06-04 00:19:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260604_0019"
down_revision = "20260603_0018"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    client_columns = _column_names("client_profiles")
    if "trial_subscription_used_at" not in client_columns:
        op.add_column(
            "client_profiles",
            sa.Column("trial_subscription_used_at", sa.DateTime(timezone=True), nullable=True),
        )

    subscription_columns = _column_names("subscriptions")
    if "source" not in subscription_columns:
        op.add_column("subscriptions", sa.Column("source", sa.String(length=64), nullable=True))


def downgrade() -> None:
    subscription_columns = _column_names("subscriptions")
    if "source" in subscription_columns:
        op.drop_column("subscriptions", "source")

    client_columns = _column_names("client_profiles")
    if "trial_subscription_used_at" in client_columns:
        op.drop_column("client_profiles", "trial_subscription_used_at")
