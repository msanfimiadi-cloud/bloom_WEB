"""add admin-managed categories

Revision ID: 20260510_0006
Revises: 20260509_0005
Create Date: 2026-05-10 00:05:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

DEFAULT_CATEGORIES = (
    ("krasota", "Красота"),
    ("manikyur-pedikyur", "Маникюр / педикюр"),
    ("volosy-okrashivanie", "Волосы / окрашивание"),
    ("brovi-resnitsy", "Брови / ресницы"),
    ("kosmetologiya", "Косметология"),
    ("massazh-spa", "Массаж / SPA"),
    ("fitnes-yoga", "Фитнес / йога"),
    ("zdorove", "Здоровье"),
    ("psihologiya", "Психология"),
    ("odezhda-aksessuary", "Одежда / аксессуары"),
    ("kafe-restorany", "Кафе / рестораны"),
    ("obuchenie-master-klassy", "Обучение / мастер-классы"),
    ("fotosessii", "Фотосессии"),
    ("cvety-podarki", "Цветы / подарки"),
    ("drugoe", "Другое"),
)

revision = "20260510_0006"
down_revision = "20260509_0005"
branch_labels = None
depends_on = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _index_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str], *, unique: bool = False) -> None:
    if index_name not in _index_names(table_name):
        op.create_index(index_name, table_name, columns, unique=unique)


def _seed_default_categories() -> None:
    bind = op.get_bind()
    categories_table = sa.table(
        "categories",
        sa.column("name", sa.String(length=120)),
        sa.column("slug", sa.String(length=120)),
        sa.column("is_active", sa.Boolean()),
        sa.column("sort_order", sa.Integer()),
    )
    for index, (slug, name) in enumerate(DEFAULT_CATEGORIES, start=1):
        exists = bind.execute(
            sa.select(sa.literal(1))
            .select_from(categories_table)
            .where(categories_table.c.slug == slug)
            .limit(1)
        ).first()
        if exists is None:
            bind.execute(
                categories_table.insert().values(
                    name=name,
                    slug=slug,
                    is_active=True,
                    sort_order=index,
                )
            )


def upgrade() -> None:
    table_names = _table_names()
    if "categories" not in table_names:
        op.create_table(
            "categories",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("slug", sa.String(length=120), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("slug", name="uq_categories_slug"),
        )
        table_names.add("categories")
    _create_index_if_missing("ix_categories_slug", "categories", ["slug"], unique=True)
    _seed_default_categories()


def downgrade() -> None:
    table_names = _table_names()
    if "categories" in table_names:
        op.drop_table("categories")
