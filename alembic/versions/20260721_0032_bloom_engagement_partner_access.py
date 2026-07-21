"""add Bloom engagement and partner bot access

Revision ID: 20260721_0032
Revises: 20260716_0031
"""

from alembic import op
import sqlalchemy as sa

revision = "20260721_0032"
down_revision = "20260716_0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "partner_bot_accesses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("partner_id", sa.Integer(), sa.ForeignKey("partners.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_user_id", sa.String(255), nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("activation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_partner_bot_access_provider_user"),
    )
    for column in ("partner_id", "provider", "provider_user_id", "is_active"):
        op.create_index(f"ix_partner_bot_accesses_{column}", "partner_bot_accesses", [column])

    op.create_table(
        "partner_code_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("access_id", sa.Integer(), sa.ForeignKey("partner_bot_accesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("was_successful", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_partner_code_attempts_access_id", "partner_code_attempts", ["access_id"])
    op.create_index("ix_partner_code_attempts_attempted_at", "partner_code_attempts", ["attempted_at"])

    op.create_table(
        "bloom_daily_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("petals", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("starts_on", sa.Date(), nullable=True),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for column in ("is_active", "starts_on", "ends_on"):
        op.create_index(f"ix_bloom_daily_tasks_{column}", "bloom_daily_tasks", [column])

    op.create_table(
        "bloom_petal_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("bloom_daily_tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("month_start", sa.Date(), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("idempotency_key", sa.String(96), nullable=False),
        sa.Column("petals", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("client_id", "idempotency_key", name="uq_bloom_petal_event_client_key"),
    )
    for column in ("client_id", "task_id", "event_date", "month_start", "source"):
        op.create_index(f"ix_bloom_petal_events_{column}", "bloom_petal_events", [column])

    op.create_table(
        "bloom_leaderboard_rewards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("month_start", sa.Date(), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("giveaway_id", sa.Integer(), sa.ForeignKey("giveaways.id", ondelete="CASCADE"), nullable=False),
        sa.Column("place", sa.Integer(), nullable=False),
        sa.Column("entries_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("month_start", "client_id", name="uq_bloom_leaderboard_reward_month_client"),
    )
    for column in ("month_start", "client_id", "giveaway_id"):
        op.create_index(f"ix_bloom_leaderboard_rewards_{column}", "bloom_leaderboard_rewards", [column])

    with op.batch_alter_table("privilege_verification_sessions") as batch:
        batch.add_column(sa.Column("confirmed_by_bot_access_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_pvs_confirmed_by_bot_access", "partner_bot_accesses", ["confirmed_by_bot_access_id"], ["id"], ondelete="SET NULL")
        batch.create_index("ix_privilege_verification_sessions_confirmed_by_bot_access_id", ["confirmed_by_bot_access_id"])

    with op.batch_alter_table("giveaway_numbers") as batch:
        batch.add_column(sa.Column("source_reference", sa.String(96), nullable=True))
        batch.create_index("ix_giveaway_numbers_source_reference", ["source_reference"])
        batch.create_unique_constraint("uq_giveaway_numbers_source_reference", ["giveaway_id", "source", "source_reference"])


def downgrade() -> None:
    with op.batch_alter_table("giveaway_numbers") as batch:
        batch.drop_constraint("uq_giveaway_numbers_source_reference", type_="unique")
        batch.drop_index("ix_giveaway_numbers_source_reference")
        batch.drop_column("source_reference")
    with op.batch_alter_table("privilege_verification_sessions") as batch:
        batch.drop_index("ix_privilege_verification_sessions_confirmed_by_bot_access_id")
        batch.drop_constraint("fk_pvs_confirmed_by_bot_access", type_="foreignkey")
        batch.drop_column("confirmed_by_bot_access_id")
    for table in ("bloom_leaderboard_rewards", "bloom_petal_events", "bloom_daily_tasks", "partner_code_attempts", "partner_bot_accesses"):
        op.drop_table(table)
