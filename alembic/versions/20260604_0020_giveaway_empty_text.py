"""add giveaway empty text setting

Revision ID: 20260604_0020
Revises: 20260604_0019
Create Date: 2026-06-04 00:20:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260604_0020"
down_revision = "20260604_0019"
branch_labels = None
depends_on = None

DEFAULT_GIVEAWAY_EMPTY_TEXT = "Информация о призах появится после настройки розыгрыша."


def upgrade() -> None:
    op.add_column(
        "landing_settings",
        sa.Column(
            "giveaway_empty_text",
            sa.String(length=512),
            nullable=False,
            server_default=DEFAULT_GIVEAWAY_EMPTY_TEXT,
        ),
    )


def downgrade() -> None:
    op.drop_column("landing_settings", "giveaway_empty_text")
