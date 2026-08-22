"""add client interaction analytics events

Revision ID: 20260822_0046
Revises: 20260821_0045
"""

from alembic import op
import sqlalchemy as sa


revision = "20260822_0046"
down_revision = "20260821_0045"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_analytics_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column("offer_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("target", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["client_id"], ["client_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["partner_id"], ["partners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["offer_id"], ["partner_offers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("client_id", "partner_id", "offer_id", "event_type", "created_at"):
        op.create_index(f"ix_client_analytics_events_{column}", "client_analytics_events", [column])
    op.create_index(
        "ix_client_analytics_events_partner_type_created",
        "client_analytics_events",
        ["partner_id", "event_type", "created_at"],
    )
    op.create_index(
        "ix_client_analytics_events_offer_type_created",
        "client_analytics_events",
        ["offer_id", "event_type", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_client_analytics_events_offer_type_created", table_name="client_analytics_events")
    op.drop_index("ix_client_analytics_events_partner_type_created", table_name="client_analytics_events")
    for column in ("created_at", "event_type", "offer_id", "partner_id", "client_id"):
        op.drop_index(f"ix_client_analytics_events_{column}", table_name="client_analytics_events")
    op.drop_table("client_analytics_events")
