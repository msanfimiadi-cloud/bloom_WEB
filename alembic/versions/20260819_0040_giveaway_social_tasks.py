"""add giveaway social tasks

Revision ID: 20260819_0040
Revises: 20260728_0039
"""

from alembic import op
import sqlalchemy as sa


revision = "20260819_0040"
down_revision = "20260728_0039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "giveaway_social_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("giveaway_id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False, server_default="subscription"),
        sa.Column("title", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("community_url", sa.String(length=512), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("reward_numbers", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["giveaway_id"], ["giveaways.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("giveaway_id", "platform", "external_id", name="uq_giveaway_social_tasks_platform_external"),
    )
    op.create_index("ix_giveaway_social_tasks_giveaway_id", "giveaway_social_tasks", ["giveaway_id"], unique=False)
    op.create_index("ix_giveaway_social_tasks_platform", "giveaway_social_tasks", ["platform"], unique=False)
    op.create_index("ix_giveaway_social_tasks_is_active", "giveaway_social_tasks", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_giveaway_social_tasks_is_active", table_name="giveaway_social_tasks")
    op.drop_index("ix_giveaway_social_tasks_platform", table_name="giveaway_social_tasks")
    op.drop_index("ix_giveaway_social_tasks_giveaway_id", table_name="giveaway_social_tasks")
    op.drop_table("giveaway_social_tasks")
