"""multi city skeleton

Revision ID: 20260508_0002
Revises: 20260430_0001
Create Date: 2026-05-08 00:02:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260508_0002"
down_revision = "20260430_0001"
branch_labels = None
depends_on = None

DEFAULT_CITIES = (
    {"name": "Новосибирск", "slug": "novosibirsk", "sort_order": 10},
    {"name": "Москва", "slug": "moscow", "sort_order": 20},
    {"name": "Санкт-Петербург", "slug": "saint-petersburg", "sort_order": 30},
    {"name": "Екатеринбург", "slug": "ekaterinburg", "sort_order": 40},
    {"name": "Казань", "slug": "kazan", "sort_order": 50},
)


def upgrade() -> None:
    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("slug", name="uq_cities_slug"),
    )

    cities_table = sa.table(
        "cities",
        sa.column("name", sa.String()),
        sa.column("slug", sa.String()),
        sa.column("is_active", sa.Boolean()),
        sa.column("sort_order", sa.Integer()),
    )
    op.bulk_insert(
        cities_table,
        [{**city, "is_active": True} for city in DEFAULT_CITIES],
    )

    inspector = sa.inspect(op.get_bind())
    table_names = set(inspector.get_table_names())

    if "partners" in table_names:
        op.add_column("partners", sa.Column("city_id", sa.Integer(), nullable=True))
        op.create_foreign_key("fk_partners_city_id_cities", "partners", "cities", ["city_id"], ["id"])
        op.create_index("ix_partners_city_id", "partners", ["city_id"])

    if "client_profiles" in table_names:
        op.add_column("client_profiles", sa.Column("selected_city_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_client_profiles_selected_city_id_cities",
            "client_profiles",
            "cities",
            ["selected_city_id"],
            ["id"],
        )
        op.create_index("ix_client_profiles_selected_city_id", "client_profiles", ["selected_city_id"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_names = set(inspector.get_table_names())

    if "client_profiles" in table_names:
        op.drop_index("ix_client_profiles_selected_city_id", table_name="client_profiles")
        op.drop_constraint("fk_client_profiles_selected_city_id_cities", "client_profiles", type_="foreignkey")
        op.drop_column("client_profiles", "selected_city_id")

    if "partners" in table_names:
        op.drop_index("ix_partners_city_id", table_name="partners")
        op.drop_constraint("fk_partners_city_id_cities", "partners", type_="foreignkey")
        op.drop_column("partners", "city_id")

    if "cities" in table_names:
        op.drop_table("cities")
