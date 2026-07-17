"""add referrals and giveaway entries

Revision ID: 20260630_0024
Revises: 20260606_0023
Create Date: 2026-06-30 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260630_0024"
down_revision = "20260606_0023"
branch_labels = None
depends_on = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _columns(table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def _indexes(table: str) -> set[str]:
    return {i["name"] for i in sa.inspect(op.get_bind()).get_indexes(table)}


def _uniques(table: str) -> set[str]:
    return {u["name"] for u in sa.inspect(op.get_bind()).get_unique_constraints(table) if u.get("name")}


def upgrade() -> None:
    tables = _table_names()
    if "client_referrals" not in tables:
        op.create_table(
            "client_referrals",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("referrer_client_id", sa.Integer(), nullable=False),
            sa.Column("referred_client_id", sa.Integer(), nullable=False),
            sa.Column("referral_code", sa.String(length=32), nullable=False),
            sa.Column("reward_entries_count", sa.Integer(), nullable=False, server_default="5"),
            sa.Column("reward_granted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["referrer_client_id"], ["client_profiles.id"]),
            sa.ForeignKeyConstraint(["referred_client_id"], ["client_profiles.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("referred_client_id", name="uq_client_referrals_referred_client_id"),
        )
    if "giveaway_entries" not in tables:
        op.create_table(
            "giveaway_entries",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("client_id", sa.Integer(), nullable=False),
            sa.Column("giveaway_id", sa.Integer(), nullable=True),
            sa.Column("source", sa.String(length=32), nullable=False, server_default="other"),
            sa.Column("entries_count", sa.Integer(), nullable=False),
            sa.Column("related_referral_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["client_id"], ["client_profiles.id"]),
            sa.ForeignKeyConstraint(["related_referral_id"], ["client_referrals.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("related_referral_id", name="uq_giveaway_entries_related_referral_id"),
        )
    for table, mapping in {
        "client_referrals": {"ix_client_referrals_referrer_client_id": ["referrer_client_id"], "ix_client_referrals_referred_client_id": ["referred_client_id"], "ix_client_referrals_referral_code": ["referral_code"]},
        "giveaway_entries": {"ix_giveaway_entries_client_id": ["client_id"], "ix_giveaway_entries_giveaway_id": ["giveaway_id"], "ix_giveaway_entries_source": ["source"]},
    }.items():
        indexes = _indexes(table)
        for name, cols in mapping.items():
            if name not in indexes:
                op.create_index(name, table, cols, unique=False)
    cols = _columns("client_profiles")
    bind = op.get_bind()
    needs_referral_code = "referral_code" not in cols
    needs_referred_by = "referred_by_referral_id" not in cols
    needs_referred_unique = "uq_client_profiles_referred_by_referral_id" not in _uniques("client_profiles")
    if bind.dialect.name == "sqlite" and (needs_referral_code or needs_referred_by or needs_referred_unique):
        with op.batch_alter_table("client_profiles") as batch_op:
            if needs_referral_code:
                batch_op.add_column(sa.Column("referral_code", sa.String(length=32), nullable=True))
            if needs_referred_by:
                batch_op.add_column(sa.Column("referred_by_referral_id", sa.Integer(), nullable=True))
                batch_op.create_foreign_key("fk_client_profiles_referred_by_referral_id", "client_referrals", ["referred_by_referral_id"], ["id"])
            if needs_referred_unique:
                batch_op.create_unique_constraint("uq_client_profiles_referred_by_referral_id", ["referred_by_referral_id"])
    else:
        if needs_referral_code:
            op.add_column("client_profiles", sa.Column("referral_code", sa.String(length=32), nullable=True))
        if needs_referred_by:
            op.add_column("client_profiles", sa.Column("referred_by_referral_id", sa.Integer(), nullable=True))
            op.create_foreign_key("fk_client_profiles_referred_by_referral_id", "client_profiles", "client_referrals", ["referred_by_referral_id"], ["id"])
        if needs_referred_unique:
            op.create_unique_constraint("uq_client_profiles_referred_by_referral_id", "client_profiles", ["referred_by_referral_id"])
    indexes = _indexes("client_profiles")
    if "ix_client_profiles_referral_code" not in indexes:
        op.create_index("ix_client_profiles_referral_code", "client_profiles", ["referral_code"], unique=True)


def downgrade() -> None:
    cols = _columns("client_profiles")
    if "referral_code" in cols and "ix_client_profiles_referral_code" in _indexes("client_profiles"):
        op.drop_index("ix_client_profiles_referral_code", table_name="client_profiles")
    bind = op.get_bind()
    if bind.dialect.name == "sqlite" and ("referred_by_referral_id" in cols or "referral_code" in cols):
        with op.batch_alter_table("client_profiles") as batch_op:
            if "referred_by_referral_id" in cols:
                batch_op.drop_constraint("uq_client_profiles_referred_by_referral_id", type_="unique")
                batch_op.drop_constraint("fk_client_profiles_referred_by_referral_id", type_="foreignkey")
                batch_op.drop_column("referred_by_referral_id")
            if "referral_code" in cols:
                batch_op.drop_column("referral_code")
    else:
        if "referred_by_referral_id" in cols:
            op.drop_constraint("uq_client_profiles_referred_by_referral_id", "client_profiles", type_="unique")
            op.drop_constraint("fk_client_profiles_referred_by_referral_id", "client_profiles", type_="foreignkey")
            op.drop_column("client_profiles", "referred_by_referral_id")
        if "referral_code" in cols:
            op.drop_column("client_profiles", "referral_code")
    if "giveaway_entries" in _table_names():
        op.drop_table("giveaway_entries")
    if "client_referrals" in _table_names():
        op.drop_table("client_referrals")
