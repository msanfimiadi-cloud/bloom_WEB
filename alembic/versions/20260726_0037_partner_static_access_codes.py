"""add static access codes for partner cabinets

Revision ID: 20260726_0037
Revises: 20260725_0036
"""

from alembic import op
import sqlalchemy as sa


revision = "20260726_0037"
down_revision = "20260725_0036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("partners") as batch:
        batch.add_column(sa.Column("access_code_digest", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("access_code_hash", sa.String(length=255), nullable=True))
        batch.create_unique_constraint("uq_partners_access_code_digest", ["access_code_digest"])
        batch.create_index("ix_partners_access_code_digest", ["access_code_digest"])


def downgrade() -> None:
    with op.batch_alter_table("partners") as batch:
        batch.drop_index("ix_partners_access_code_digest")
        batch.drop_constraint("uq_partners_access_code_digest", type_="unique")
        batch.drop_column("access_code_hash")
        batch.drop_column("access_code_digest")
