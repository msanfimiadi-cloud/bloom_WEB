"""add landing settings

Revision ID: 20260601_0015
Revises: 20260525_0014
Create Date: 2026-06-01 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260601_0015"
down_revision = "20260525_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "landing_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("members_count_base", sa.Integer(), nullable=False, server_default="125"),
        sa.Column("partners_count_display", sa.Integer(), nullable=False, server_default="18"),
        sa.Column("savings_total", sa.Integer(), nullable=False, server_default="53500"),
        sa.Column("giveaway_title", sa.String(length=255), nullable=False, server_default="Розыгрыш месяца"),
        sa.Column("giveaway_current", sa.String(length=255), nullable=False, server_default="Приз месяца"),
        sa.Column("giveaway_subtitle", sa.String(length=512), nullable=False, server_default="доступно участницам клуба"),
        sa.Column("giveaway_items", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.execute(
        "INSERT INTO landing_settings (id, members_count_base, partners_count_display, savings_total, giveaway_title, giveaway_current, giveaway_subtitle, giveaway_items) "
        "VALUES (1, 125, 18, 53500, 'Розыгрыш месяца', 'Приз месяца', 'доступно участницам клуба', '[{\"title\": \"Приз месяца\", \"is_active\": true, \"sort_order\": 0}]')"
    )


def downgrade() -> None:
    op.drop_table("landing_settings")
