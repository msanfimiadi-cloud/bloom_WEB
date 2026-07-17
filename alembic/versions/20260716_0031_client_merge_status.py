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
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("client_profiles") as batch_op:
            batch_op.add_column(sa.Column("status", sa.String(length=32), server_default="active", nullable=False))
            batch_op.add_column(sa.Column("merged_into_client_id", sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column("merged_at", sa.DateTime(timezone=True), nullable=True))
            batch_op.create_foreign_key("fk_client_profiles_merged_into_client_id", "client_profiles", ["merged_into_client_id"], ["id"])
    else:
        op.add_column("client_profiles", sa.Column("status", sa.String(length=32), server_default="active", nullable=False))
        op.add_column("client_profiles", sa.Column("merged_into_client_id", sa.Integer(), nullable=True))
        op.add_column("client_profiles", sa.Column("merged_at", sa.DateTime(timezone=True), nullable=True))
        op.create_foreign_key("fk_client_profiles_merged_into_client_id", "client_profiles", "client_profiles", ["merged_into_client_id"], ["id"])
    op.create_index(op.f("ix_client_profiles_status"), "client_profiles", ["status"], unique=False)
    op.create_index(op.f("ix_client_profiles_merged_into_client_id"), "client_profiles", ["merged_into_client_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_client_profiles_merged_into_client_id"), table_name="client_profiles")
    op.drop_index(op.f("ix_client_profiles_status"), table_name="client_profiles")
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("client_profiles") as batch_op:
            batch_op.drop_constraint("fk_client_profiles_merged_into_client_id", type_="foreignkey")
            batch_op.drop_column("merged_at")
            batch_op.drop_column("merged_into_client_id")
            batch_op.drop_column("status")
    else:
        op.drop_constraint("fk_client_profiles_merged_into_client_id", "client_profiles", type_="foreignkey")
        op.drop_column("client_profiles", "merged_at")
        op.drop_column("client_profiles", "merged_into_client_id")
        op.drop_column("client_profiles", "status")
