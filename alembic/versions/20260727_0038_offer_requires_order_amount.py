"""add explicit variable order amount flag to partner offers

Revision ID: 20260727_0038
Revises: 20260726_0037
Create Date: 2026-07-27
"""

from alembic import op
import sqlalchemy as sa


revision = "20260727_0038"
down_revision = "20260726_0037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("partner_offers") as batch:
        batch.add_column(
            sa.Column(
                "requires_order_amount",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )

    op.execute(
        sa.text(
            """
            UPDATE partner_offers
            SET requires_order_amount = true
            WHERE base_price IS NULL
              AND discount_percent IS NOT NULL
              AND discount_percent > 0
              AND discount_percent <= 100
            """
        )
    )


def downgrade() -> None:
    with op.batch_alter_table("partner_offers") as batch:
        batch.drop_column("requires_order_amount")
