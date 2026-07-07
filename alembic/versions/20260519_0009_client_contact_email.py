"""add client contact email

Revision ID: 20260519_0009
Revises: 20260514_0008
Create Date: 2026-05-19
"""

from alembic import op
import sqlalchemy as sa


revision = "20260519_0009"
down_revision = "20260514_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("client_profiles", sa.Column("contact_email", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_client_profiles_contact_email"), "client_profiles", ["contact_email"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_client_profiles_contact_email"), table_name="client_profiles")
    op.drop_column("client_profiles", "contact_email")
