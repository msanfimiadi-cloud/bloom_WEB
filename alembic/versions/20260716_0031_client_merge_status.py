"""client merge status

Revision ID: 20260716_0031
Revises: 20260716_0030
Create Date: 2026-07-16
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260716_0031"
down_revision = "20260716_0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("client_profiles", sa.Column("status", sa.String(length=32), server_default="active", nullable=False))
    op.add_column("client_profiles", sa.Column("merged_into_client_id", sa.Integer(), nullable=True))
    op.add_column("client_profiles", sa.Column("merged_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_client_profiles_status"), "client_profiles", ["status"], unique=False)
    op.create_index(op.f("ix_client_profiles_merged_into_client_id"), "client_profiles", ["merged_into_client_id"], unique=False)
    op.create_foreign_key("fk_client_profiles_merged_into_client_id", "client_profiles", "client_profiles", ["merged_into_client_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_client_profiles_merged_into_client_id", "client_profiles", type_="foreignkey")
    op.drop_index(op.f("ix_client_profiles_merged_into_client_id"), table_name="client_profiles")
    op.drop_index(op.f("ix_client_profiles_status"), table_name="client_profiles")
    op.drop_column("client_profiles", "merged_at")
    op.drop_column("client_profiles", "merged_into_client_id")
    op.drop_column("client_profiles", "status")
