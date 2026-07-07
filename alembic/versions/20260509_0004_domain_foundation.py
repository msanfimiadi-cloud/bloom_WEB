"""domain foundation models

Revision ID: 20260509_0004
Revises: 20260508_0003
Create Date: 2026-05-09 00:04:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260509_0004"
down_revision = "20260508_0003"
branch_labels = None
depends_on = None

MVP_CITIES = (
    {"name": "Новосибирск", "slug": "novosibirsk", "sort_order": 10},
    {"name": "Череповец", "slug": "cherepovets", "sort_order": 20},
)


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _index_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str], *, unique: bool = False) -> None:
    if index_name not in _index_names(table_name):
        op.create_index(index_name, table_name, columns, unique=unique)


def _seed_mvp_cities() -> None:
    bind = op.get_bind()
    cities_table = sa.table(
        "cities",
        sa.column("name", sa.String(length=120)),
        sa.column("slug", sa.String(length=120)),
        sa.column("is_active", sa.Boolean()),
        sa.column("sort_order", sa.Integer()),
    )
    for city in MVP_CITIES:
        exists = bind.execute(
            sa.select(sa.literal(1)).select_from(cities_table).where(cities_table.c.slug == city["slug"]).limit(1)
        ).first()
        if exists is None:
            bind.execute(cities_table.insert().values(**city, is_active=True))


def upgrade() -> None:
    table_names = _table_names()

    if "cities" not in table_names:
        op.create_table(
            "cities",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("slug", sa.String(length=120), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("name", name="uq_cities_name"),
            sa.UniqueConstraint("slug", name="uq_cities_slug"),
        )
        table_names.add("cities")
    _create_index_if_missing("ix_cities_name", "cities", ["name"])
    _create_index_if_missing("ix_cities_slug", "cities", ["slug"], unique=True)
    _seed_mvp_cities()

    if "users" not in table_names:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("email", sa.String(length=255), nullable=True),
            sa.Column("phone", sa.String(length=64), nullable=True),
            sa.Column("password_hash", sa.String(length=255), nullable=True),
            sa.Column("role", sa.String(length=32), nullable=False, server_default="client"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("email", name="uq_users_email"),
            sa.UniqueConstraint("phone", name="uq_users_phone"),
        )
        op.create_index("ix_users_email", "users", ["email"])
        op.create_index("ix_users_phone", "users", ["phone"])
        table_names.add("users")

    if "client_profiles" not in table_names:
        op.create_table(
            "client_profiles",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("selected_city_id", sa.Integer(), sa.ForeignKey("cities.id"), nullable=True),
            sa.Column("full_name", sa.String(length=255), nullable=True),
            sa.Column("vk_user_id", sa.String(length=255), nullable=True),
            sa.Column("source", sa.String(length=64), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("user_id", name="uq_client_profiles_user_id"),
            sa.UniqueConstraint("vk_user_id", name="uq_client_profiles_vk_user_id"),
        )
        op.create_index("ix_client_profiles_vk_user_id", "client_profiles", ["vk_user_id"])
        table_names.add("client_profiles")

    if "partners" not in table_names:
        op.create_table(
            "partners",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("city_id", sa.Integer(), sa.ForeignKey("cities.id"), nullable=False),
            sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("category_slug", sa.String(length=120), nullable=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("address", sa.String(length=255), nullable=True),
            sa.Column("phone", sa.String(length=64), nullable=True),
            sa.Column("website_url", sa.String(length=512), nullable=True),
            sa.Column("social_url", sa.String(length=512), nullable=True),
            sa.Column("working_hours", sa.String(length=255), nullable=True),
            sa.Column("logo_url", sa.String(length=512), nullable=True),
            sa.Column("cover_url", sa.String(length=512), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_partners_city_id", "partners", ["city_id"])
        op.create_index("ix_partners_category_slug", "partners", ["category_slug"])
        table_names.add("partners")

    if "partner_offers" not in table_names:
        op.create_table(
            "partner_offers",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("partner_id", sa.Integer(), sa.ForeignKey("partners.id"), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("benefit_text", sa.String(length=255), nullable=True),
            sa.Column("conditions", sa.Text(), nullable=True),
            sa.Column("base_price", sa.Numeric(12, 2), nullable=True),
            sa.Column("discount_percent", sa.Numeric(5, 2), nullable=True),
            sa.Column("image_url", sa.String(length=512), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_partner_offers_partner_id", "partner_offers", ["partner_id"])
        table_names.add("partner_offers")

    if "payment_requests" not in table_names:
        op.create_table(
            "payment_requests",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("client_id", sa.Integer(), sa.ForeignKey("client_profiles.id"), nullable=False),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("source", sa.String(length=64), nullable=True),
            sa.Column("comment", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("admin_user_id", sa.Integer(), sa.ForeignKey("admin_users.id"), nullable=True),
            sa.Column("access_until", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_payment_requests_client_id", "payment_requests", ["client_id"])
        table_names.add("payment_requests")

    if "payment_receipts" not in table_names:
        op.create_table(
            "payment_receipts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("payment_request_id", sa.Integer(), sa.ForeignKey("payment_requests.id"), nullable=False),
            sa.Column("file_url", sa.String(length=512), nullable=False),
            sa.Column("uploaded_via", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_payment_receipts_payment_request_id", "payment_receipts", ["payment_request_id"])
        table_names.add("payment_receipts")

    if "subscriptions" not in table_names:
        op.create_table(
            "subscriptions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("client_id", sa.Integer(), sa.ForeignKey("client_profiles.id"), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
            sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("source_payment_request_id", sa.Integer(), sa.ForeignKey("payment_requests.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_subscriptions_client_id", "subscriptions", ["client_id"])
        table_names.add("subscriptions")

    if "partner_qr_links" not in table_names:
        op.create_table(
            "partner_qr_links",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("partner_id", sa.Integer(), sa.ForeignKey("partners.id"), nullable=False),
            sa.Column("slug", sa.String(length=120), nullable=False),
            sa.Column("deep_link_payload", sa.String(length=512), nullable=True),
            sa.Column("target_url", sa.String(length=512), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("slug", name="uq_partner_qr_links_slug"),
        )
        op.create_index("ix_partner_qr_links_partner_id", "partner_qr_links", ["partner_id"])
        op.create_index("ix_partner_qr_links_slug", "partner_qr_links", ["slug"], unique=True)
        table_names.add("partner_qr_links")

    if "lead_clicks" not in table_names:
        op.create_table(
            "lead_clicks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("partner_id", sa.Integer(), sa.ForeignKey("partners.id"), nullable=True),
            sa.Column("qr_link_id", sa.Integer(), sa.ForeignKey("partner_qr_links.id"), nullable=True),
            sa.Column("city_id", sa.Integer(), sa.ForeignKey("cities.id"), nullable=True),
            sa.Column("source", sa.String(length=64), nullable=True),
            sa.Column("session_id", sa.String(length=255), nullable=True),
            sa.Column("ip_hash", sa.String(length=255), nullable=True),
            sa.Column("user_agent_hash", sa.String(length=255), nullable=True),
            sa.Column("referer", sa.String(length=512), nullable=True),
            sa.Column("utm_source", sa.String(length=255), nullable=True),
            sa.Column("utm_medium", sa.String(length=255), nullable=True),
            sa.Column("utm_campaign", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_lead_clicks_partner_id", "lead_clicks", ["partner_id"])
        op.create_index("ix_lead_clicks_qr_link_id", "lead_clicks", ["qr_link_id"])
        op.create_index("ix_lead_clicks_city_id", "lead_clicks", ["city_id"])
        op.create_index("ix_lead_clicks_session_id", "lead_clicks", ["session_id"])
        table_names.add("lead_clicks")

    if "privilege_verification_sessions" not in table_names:
        op.create_table(
            "privilege_verification_sessions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("client_id", sa.Integer(), sa.ForeignKey("client_profiles.id"), nullable=False),
            sa.Column("partner_id", sa.Integer(), sa.ForeignKey("partners.id"), nullable=False),
            sa.Column("offer_id", sa.Integer(), sa.ForeignKey("partner_offers.id"), nullable=True),
            sa.Column("code", sa.String(length=12), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
            sa.Column("source", sa.String(length=64), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_privilege_verification_sessions_client_id", "privilege_verification_sessions", ["client_id"])
        op.create_index("ix_privilege_verification_sessions_partner_id", "privilege_verification_sessions", ["partner_id"])
        op.create_index("ix_privilege_verification_sessions_code", "privilege_verification_sessions", ["code"])


def downgrade() -> None:
    table_names = _table_names()
    for table_name in (
        "privilege_verification_sessions",
        "lead_clicks",
        "partner_qr_links",
        "subscriptions",
        "payment_receipts",
        "payment_requests",
        "partner_offers",
        "partners",
        "client_profiles",
        "users",
    ):
        if table_name in table_names:
            op.drop_table(table_name)
