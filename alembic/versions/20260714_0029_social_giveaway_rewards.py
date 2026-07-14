"""add social giveaway rewards

Revision ID: 20260714_0029
Revises: 20260707_0028
Create Date: 2026-07-14
"""
from alembic import op
import sqlalchemy as sa

revision = "20260714_0029"
down_revision = "20260707_0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("giveaways") as batch:
        batch.add_column(sa.Column("telegram_community_url", sa.String(length=512), nullable=True))
        batch.add_column(sa.Column("telegram_chat_id", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("telegram_reward_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("telegram_reward_numbers", sa.Integer(), nullable=False, server_default="1"))
        batch.add_column(sa.Column("vk_community_url", sa.String(length=512), nullable=True))
        batch.add_column(sa.Column("vk_group_id", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("vk_reward_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("vk_reward_numbers", sa.Integer(), nullable=False, server_default="1"))
    with op.batch_alter_table("giveaway_numbers") as batch:
        batch.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch.add_column(sa.Column("status", sa.String(length=32), nullable=False, server_default="active"))
        batch.add_column(sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("deactivation_reason", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("verification_platform", sa.String(length=32), nullable=True))
        batch.add_column(sa.Column("external_community_id", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("reactivated_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_index("ix_giveaway_numbers_is_active", ["is_active"])
        batch.create_index("ix_giveaway_numbers_status", ["status"])


def downgrade() -> None:
    with op.batch_alter_table("giveaway_numbers") as batch:
        batch.drop_index("ix_giveaway_numbers_status")
        batch.drop_index("ix_giveaway_numbers_is_active")
        for column in ("reactivated_at", "external_community_id", "verification_platform", "verified_at", "deactivation_reason", "deactivated_at", "status", "is_active"):
            batch.drop_column(column)
    with op.batch_alter_table("giveaways") as batch:
        for column in ("vk_reward_numbers", "vk_reward_enabled", "vk_group_id", "vk_community_url", "telegram_reward_numbers", "telegram_reward_enabled", "telegram_chat_id", "telegram_community_url"):
            batch.drop_column(column)
