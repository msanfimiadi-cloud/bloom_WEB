"""Add confirmed_by_partner_id to privilege verification sessions.

Revision ID: 20260602_0017
Revises: 20260602_0016
Create Date: 2026-06-02 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260602_0017"
down_revision = "20260602_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("privilege_verification_sessions", sa.Column("confirmed_by_partner_id", sa.Integer(), nullable=True))
    op.create_index(
        "ix_privilege_verification_sessions_confirmed_by_partner_id",
        "privilege_verification_sessions",
        ["confirmed_by_partner_id"],
    )
    op.create_foreign_key(
        "fk_pvs_confirmed_by_partner",
        "privilege_verification_sessions",
        "partners",
        ["confirmed_by_partner_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_pvs_confirmed_by_partner",
        "privilege_verification_sessions",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_privilege_verification_sessions_confirmed_by_partner_id",
        table_name="privilege_verification_sessions",
    )
    op.drop_column("privilege_verification_sessions", "confirmed_by_partner_id")
