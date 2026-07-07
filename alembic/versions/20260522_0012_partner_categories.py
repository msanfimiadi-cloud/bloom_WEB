"""add partner_categories m2m with backfill from partners.category_slug

Revision ID: 20260522_0012
Revises: 20260521_0011
Create Date: 2026-05-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260522_0012"
down_revision = "20260521_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "partner_categories",
        sa.Column("partner_id", sa.Integer(), sa.ForeignKey("partners.id"), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("partner_id", "category_id", name="uq_partner_categories_partner_category"),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO partner_categories (partner_id, category_id)
            SELECT p.id, c.id
            FROM partners p
            JOIN categories c ON c.slug = p.category_slug
            WHERE p.category_slug IS NOT NULL AND btrim(p.category_slug) <> ''
            ON CONFLICT (partner_id, category_id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.drop_table("partner_categories")
