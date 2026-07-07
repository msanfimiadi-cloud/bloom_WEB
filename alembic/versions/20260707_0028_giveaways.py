"""add giveaways

Revision ID: 20260707_0028
Revises: 20260706_0027_merge_heads
Create Date: 2026-07-07
"""
from alembic import op
import sqlalchemy as sa

revision = "20260707_0028"
down_revision = "20260706_0027_merge_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "giveaways",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("winners_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_giveaways_is_active", "giveaways", ["is_active"])
    op.create_index("ix_giveaways_starts_at", "giveaways", ["starts_at"])
    op.create_index("ix_giveaways_ends_at", "giveaways", ["ends_at"])
    op.create_table(
        "giveaway_prizes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("giveaway_id", sa.Integer(), sa.ForeignKey("giveaways.id", ondelete="CASCADE"), nullable=False),
        sa.Column("place_number", sa.Integer(), nullable=False),
        sa.Column("prize_title", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("winner_provider", sa.String(length=32), nullable=True),
        sa.Column("winner_provider_user_id", sa.String(length=255), nullable=True),
        sa.Column("winning_number", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("giveaway_id", "place_number", name="uq_giveaway_prizes_giveaway_place"),
    )
    op.create_index("ix_giveaway_prizes_giveaway_id", "giveaway_prizes", ["giveaway_id"])
    op.create_table(
        "giveaway_numbers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("giveaway_id", sa.Integer(), sa.ForeignKey("giveaways.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("number", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="subscription"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("giveaway_id", "number", name="uq_giveaway_numbers_giveaway_number"),
        sa.UniqueConstraint("giveaway_id", "client_id", "number", name="uq_giveaway_numbers_client_number"),
    )
    op.create_index("ix_giveaway_numbers_giveaway_id", "giveaway_numbers", ["giveaway_id"])
    op.create_index("ix_giveaway_numbers_client_id", "giveaway_numbers", ["client_id"])
    op.create_index("ix_giveaway_numbers_number", "giveaway_numbers", ["number"])


def downgrade() -> None:
    op.drop_table("giveaway_numbers")
    op.drop_table("giveaway_prizes")
    op.drop_table("giveaways")
