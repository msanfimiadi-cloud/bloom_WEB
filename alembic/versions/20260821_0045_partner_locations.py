"""add partner locations and bind offers/verifications to branches

Revision ID: 20260821_0045
Revises: 20260811_0044
"""

from alembic import op
import sqlalchemy as sa


revision = "20260821_0045"
down_revision = "20260811_0044"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "partner_locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("map_url", sa.String(length=512), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("working_hours", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["partner_id"], ["partners.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_partner_locations_partner_id"), "partner_locations", ["partner_id"], unique=False)

    op.add_column("partner_offers", sa.Column("location_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_partner_offers_location_id"), "partner_offers", ["location_id"], unique=False)
    op.create_foreign_key(
        "fk_partner_offers_location_id_partner_locations",
        "partner_offers",
        "partner_locations",
        ["location_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("privilege_verification_sessions", sa.Column("location_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_privilege_verification_sessions_location_id"),
        "privilege_verification_sessions",
        ["location_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_privilege_verification_sessions_location_id_partner_locations",
        "privilege_verification_sessions",
        "partner_locations",
        ["location_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_privilege_verification_sessions_location_id_partner_locations",
        "privilege_verification_sessions",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_privilege_verification_sessions_location_id"), table_name="privilege_verification_sessions")
    op.drop_column("privilege_verification_sessions", "location_id")

    op.drop_constraint(
        "fk_partner_offers_location_id_partner_locations",
        "partner_offers",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_partner_offers_location_id"), table_name="partner_offers")
    op.drop_column("partner_offers", "location_id")

    op.drop_index(op.f("ix_partner_locations_partner_id"), table_name="partner_locations")
    op.drop_table("partner_locations")
