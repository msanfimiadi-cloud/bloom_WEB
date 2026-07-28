"""add partner analytics reset and offer archive

Revision ID: 20260728_0039
Revises: 20260727_0038
"""

from alembic import op
import sqlalchemy as sa


revision = "20260728_0039"
down_revision = "20260727_0038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("partners", sa.Column("analytics_reset_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("partner_offers", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_partner_offers_deleted_at", "partner_offers", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_partner_offers_deleted_at", table_name="partner_offers")
    op.drop_column("partner_offers", "deleted_at")
    op.drop_column("partners", "analytics_reset_at")
