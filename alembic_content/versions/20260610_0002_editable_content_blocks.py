"""support editable content blocks

Revision ID: 20260610_0002
Revises: 20260610_0001
Create Date: 2026-06-10 12:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260610_0002"
down_revision = "20260610_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_content_blocks_slug", table_name="content_blocks")
    with op.batch_alter_table("content_blocks") as batch_op:
        batch_op.alter_column("slug", new_column_name="key", existing_type=sa.String(length=120), nullable=False)
        batch_op.alter_column(
            "block_type",
            new_column_name="placement",
            existing_type=sa.String(length=120),
            nullable=False,
        )
        batch_op.alter_column("payload", new_column_name="metadata_json", existing_type=sa.JSON(), nullable=True)
        batch_op.add_column(sa.Column("locale", sa.String(length=16), nullable=False, server_default="ru"))
        batch_op.drop_column("subtitle")
        batch_op.drop_column("sort_order")
        batch_op.create_unique_constraint("uq_content_blocks_key_locale", ["key", "locale"])
    op.create_index("ix_content_blocks_key", "content_blocks", ["key"])
    op.create_index("ix_content_blocks_locale", "content_blocks", ["locale"])
    op.create_index("ix_content_blocks_placement", "content_blocks", ["placement"])


def downgrade() -> None:
    op.drop_index("ix_content_blocks_placement", table_name="content_blocks")
    op.drop_index("ix_content_blocks_locale", table_name="content_blocks")
    op.drop_index("ix_content_blocks_key", table_name="content_blocks")
    with op.batch_alter_table("content_blocks") as batch_op:
        batch_op.drop_constraint("uq_content_blocks_key_locale", type_="unique")
        batch_op.add_column(sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("subtitle", sa.String(length=512), nullable=True))
        batch_op.drop_column("locale")
        batch_op.alter_column("metadata_json", new_column_name="payload", existing_type=sa.JSON(), nullable=True)
        batch_op.alter_column(
            "placement",
            new_column_name="block_type",
            existing_type=sa.String(length=120),
            nullable=False,
        )
        batch_op.alter_column("key", new_column_name="slug", existing_type=sa.String(length=120), nullable=False)
        batch_op.create_unique_constraint("uq_content_blocks_slug", ["slug"])
    op.create_index("ix_content_blocks_slug", "content_blocks", ["slug"], unique=True)
