"""create content database tables

Revision ID: 20260610_0001
Revises:
Create Date: 2026-06-10 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260610_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content_cities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_content_cities_name", "content_cities", ["name"], unique=True)
    op.create_index("ix_content_cities_slug", "content_cities", ["slug"], unique=True)

    op.create_table(
        "content_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_content_categories_slug", "content_categories", ["slug"], unique=True)

    op.create_table(
        "content_giveaways",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("current", sa.String(length=255), nullable=True),
        sa.Column("subtitle", sa.String(length=512), nullable=True),
        sa.Column("empty_text", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "content_banners",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("subtitle", sa.String(length=512), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=512), nullable=True),
        sa.Column("mobile_image_url", sa.String(length=512), nullable=True),
        sa.Column("link_url", sa.String(length=512), nullable=True),
        sa.Column("cta_text", sa.String(length=120), nullable=True),
        sa.Column("placement", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "content_blocks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("subtitle", sa.String(length=512), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("block_type", sa.String(length=120), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_content_blocks_slug", "content_blocks", ["slug"], unique=True)

    op.create_table(
        "content_partners",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("category_slug", sa.String(length=120), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("website_url", sa.String(length=512), nullable=True),
        sa.Column("social_url", sa.String(length=512), nullable=True),
        sa.Column("instagram_url", sa.String(length=512), nullable=True),
        sa.Column("vk_url", sa.String(length=512), nullable=True),
        sa.Column("telegram_url", sa.String(length=512), nullable=True),
        sa.Column("whatsapp_url", sa.String(length=512), nullable=True),
        sa.Column("map_url", sa.String(length=512), nullable=True),
        sa.Column("working_hours", sa.String(length=255), nullable=True),
        sa.Column("logo_url", sa.String(length=512), nullable=True),
        sa.Column("cover_url", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["city_id"], ["content_cities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_partners_city_id", "content_partners", ["city_id"])
    op.create_index("ix_content_partners_category_slug", "content_partners", ["category_slug"])

    op.create_table(
        "content_partner_categories",
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["content_categories.id"]),
        sa.ForeignKeyConstraint(["partner_id"], ["content_partners.id"]),
        sa.PrimaryKeyConstraint("partner_id", "category_id"),
        sa.UniqueConstraint("partner_id", "category_id", name="uq_content_partner_categories_pair"),
    )

    op.create_table(
        "content_partner_photos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("alt_text", sa.String(length=255), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["content_partners.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_partner_photos_partner_id", "content_partner_photos", ["partner_id"])

    op.create_table(
        "content_offers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("benefit_text", sa.String(length=255), nullable=True),
        sa.Column("conditions", sa.Text(), nullable=True),
        sa.Column("base_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("discount_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("image_url", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["content_partners.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_offers_partner_id", "content_offers", ["partner_id"])

    op.create_table(
        "content_giveaway_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("giveaway_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["giveaway_id"], ["content_giveaways.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_giveaway_items_giveaway_id", "content_giveaway_items", ["giveaway_id"])

    op.create_table(
        "content_offer_photos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("alt_text", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["offer_id"], ["content_offers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_offer_photos_offer_id", "content_offer_photos", ["offer_id"])


def downgrade() -> None:
    op.drop_index("ix_content_offer_photos_offer_id", table_name="content_offer_photos")
    op.drop_table("content_offer_photos")
    op.drop_index("ix_content_giveaway_items_giveaway_id", table_name="content_giveaway_items")
    op.drop_table("content_giveaway_items")
    op.drop_index("ix_content_offers_partner_id", table_name="content_offers")
    op.drop_table("content_offers")
    op.drop_index("ix_content_partner_photos_partner_id", table_name="content_partner_photos")
    op.drop_table("content_partner_photos")
    op.drop_table("content_partner_categories")
    op.drop_index("ix_content_partners_category_slug", table_name="content_partners")
    op.drop_index("ix_content_partners_city_id", table_name="content_partners")
    op.drop_table("content_partners")
    op.drop_index("ix_content_blocks_slug", table_name="content_blocks")
    op.drop_table("content_blocks")
    op.drop_table("content_banners")
    op.drop_table("content_giveaways")
    op.drop_index("ix_content_categories_slug", table_name="content_categories")
    op.drop_table("content_categories")
    op.drop_index("ix_content_cities_slug", table_name="content_cities")
    op.drop_index("ix_content_cities_name", table_name="content_cities")
    op.drop_table("content_cities")
