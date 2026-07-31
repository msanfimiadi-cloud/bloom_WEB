"""set live landing statistics baselines

Revision ID: 20260731_0041
Revises: 20260730_0040
"""

from alembic import op
import sqlalchemy as sa


revision = "20260731_0041"
down_revision = "20260730_0040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("landing_settings", "members_count_base", server_default=sa.text("20"))
    op.alter_column("landing_settings", "partners_count_display", server_default=sa.text("0"))
    op.alter_column("landing_settings", "savings_total", server_default=sa.text("8200"))
    op.execute(
        sa.text(
            "UPDATE landing_settings "
            "SET members_count_base = 20, partners_count_display = 0, savings_total = 8200 "
            "WHERE id = 1"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE landing_settings "
            "SET members_count_base = 125, partners_count_display = 18, savings_total = 53500 "
            "WHERE id = 1"
        )
    )
    op.alter_column("landing_settings", "members_count_base", server_default=sa.text("125"))
    op.alter_column("landing_settings", "partners_count_display", server_default=sa.text("18"))
    op.alter_column("landing_settings", "savings_total", server_default=sa.text("53500"))
