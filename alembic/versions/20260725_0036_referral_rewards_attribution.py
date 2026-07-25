"""add referral subscription rewards and acquisition attribution

Revision ID: 20260725_0036
Revises: 20260722_0035
"""

from alembic import op
import sqlalchemy as sa


revision = "20260725_0036"
down_revision = "20260722_0035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("client_profiles") as batch:
        batch.add_column(sa.Column("utm_source", sa.String(255), nullable=True))
        batch.add_column(sa.Column("utm_medium", sa.String(255), nullable=True))
        batch.add_column(sa.Column("utm_campaign", sa.String(255), nullable=True))
        batch.add_column(sa.Column("utm_content", sa.String(255), nullable=True))
        batch.add_column(sa.Column("utm_term", sa.String(255), nullable=True))
        batch.add_column(sa.Column("acquisition_landing_url", sa.String(1024), nullable=True))
        batch.create_index("ix_client_profiles_utm_source", ["utm_source"])
        batch.create_index("ix_client_profiles_utm_campaign", ["utm_campaign"])

    with op.batch_alter_table("client_referrals") as batch:
        batch.add_column(sa.Column("paid_qualified_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("paid_qualification_source", sa.String(96), nullable=True))
        batch.create_index("ix_client_referrals_paid_qualified_at", ["paid_qualified_at"])
        batch.create_unique_constraint("uq_client_referrals_paid_qualification_source", ["paid_qualification_source"])

    op.execute("UPDATE client_referrals SET reward_entries_count = 1 WHERE reward_entries_count <> 1")
    op.execute("UPDATE giveaway_entries SET entries_count = 1 WHERE source = 'referral' AND entries_count <> 1")

    op.create_table(
        "referral_subscription_rewards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("referrer_client_id", sa.Integer(), sa.ForeignKey("client_profiles.id"), nullable=False),
        sa.Column("reward_period", sa.Integer(), nullable=False),
        sa.Column("qualified_referrals_count", sa.Integer(), nullable=False),
        sa.Column("reward_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id"), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("referrer_client_id", "reward_period", name="uq_referral_subscription_rewards_period"),
    )
    op.create_index("ix_referral_subscription_rewards_referrer_client_id", "referral_subscription_rewards", ["referrer_client_id"])


def downgrade() -> None:
    op.drop_index("ix_referral_subscription_rewards_referrer_client_id", table_name="referral_subscription_rewards")
    op.drop_table("referral_subscription_rewards")
    with op.batch_alter_table("client_referrals") as batch:
        batch.drop_constraint("uq_client_referrals_paid_qualification_source", type_="unique")
        batch.drop_index("ix_client_referrals_paid_qualified_at")
        batch.drop_column("paid_qualification_source")
        batch.drop_column("paid_qualified_at")
    with op.batch_alter_table("client_profiles") as batch:
        batch.drop_index("ix_client_profiles_utm_campaign")
        batch.drop_index("ix_client_profiles_utm_source")
        batch.drop_column("acquisition_landing_url")
        batch.drop_column("utm_term")
        batch.drop_column("utm_content")
        batch.drop_column("utm_campaign")
        batch.drop_column("utm_medium")
        batch.drop_column("utm_source")
