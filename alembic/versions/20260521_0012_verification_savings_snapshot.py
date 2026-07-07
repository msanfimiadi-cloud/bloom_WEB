"""add savings snapshot fields to privilege verifications

Revision ID: 20260521_0012
Revises: 20260521_0011
Create Date: 2026-05-21
"""

from alembic import op
import sqlalchemy as sa

revision = "20260521_0012"
down_revision = "20260521_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("privilege_verification_sessions", sa.Column("saving_base_price", sa.Numeric(12, 2), nullable=True))
    op.add_column("privilege_verification_sessions", sa.Column("saving_final_price", sa.Numeric(12, 2), nullable=True))
    op.add_column("privilege_verification_sessions", sa.Column("saving_discount_percent", sa.Numeric(5, 2), nullable=True))
    op.add_column("privilege_verification_sessions", sa.Column("saving_amount", sa.Numeric(12, 2), nullable=True))
    op.add_column("privilege_verification_sessions", sa.Column("saving_partner_name", sa.Text(), nullable=True))
    op.add_column("privilege_verification_sessions", sa.Column("saving_offer_title", sa.Text(), nullable=True))
    op.add_column("privilege_verification_sessions", sa.Column("saving_used_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("privilege_verification_sessions", "saving_used_at")
    op.drop_column("privilege_verification_sessions", "saving_offer_title")
    op.drop_column("privilege_verification_sessions", "saving_partner_name")
    op.drop_column("privilege_verification_sessions", "saving_amount")
    op.drop_column("privilege_verification_sessions", "saving_discount_percent")
    op.drop_column("privilege_verification_sessions", "saving_final_price")
    op.drop_column("privilege_verification_sessions", "saving_base_price")
