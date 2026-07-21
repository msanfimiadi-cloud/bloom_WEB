"""add Bloom garden settings and weekly surveys

Revision ID: 20260721_0033
Revises: 20260721_0032
"""

from alembic import op
import sqlalchemy as sa


revision = "20260721_0033"
down_revision = "20260721_0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bloom_garden_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("placement_mode", sa.String(16), nullable=False, server_default="random"),
        sa.Column("manual_position", sa.String(32), nullable=False, server_default="top_right"),
        sa.Column("daily_petals", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.bulk_insert(sa.table("bloom_garden_settings", sa.column("id", sa.Integer()), sa.column("placement_mode", sa.String()), sa.column("manual_position", sa.String()), sa.column("daily_petals", sa.Integer())), [{"id": 1, "placement_mode": "random", "manual_position": "top_right", "daily_petals": 1}])

    op.create_table(
        "bloom_special_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("petals", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for column in ("starts_on", "ends_on", "is_active"):
        op.create_index(f"ix_bloom_special_tasks_{column}", "bloom_special_tasks", [column])

    op.create_table(
        "bloom_special_questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("bloom_special_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_bloom_special_questions_task_id", "bloom_special_questions", ["task_id"])
    op.create_table(
        "bloom_special_options",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("bloom_special_questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(500), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_bloom_special_options_question_id", "bloom_special_options", ["question_id"])
    op.create_table(
        "bloom_special_submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("bloom_special_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("task_id", "client_id", name="uq_bloom_special_submission_task_client"),
    )
    for column in ("task_id", "client_id", "completed_at"):
        op.create_index(f"ix_bloom_special_submissions_{column}", "bloom_special_submissions", [column])
    op.create_table(
        "bloom_special_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submission_id", sa.Integer(), sa.ForeignKey("bloom_special_submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("bloom_special_questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("option_id", sa.Integer(), sa.ForeignKey("bloom_special_options.id", ondelete="RESTRICT"), nullable=False),
        sa.UniqueConstraint("submission_id", "question_id", name="uq_bloom_special_answer_submission_question"),
    )
    for column in ("submission_id", "question_id", "option_id"):
        op.create_index(f"ix_bloom_special_answers_{column}", "bloom_special_answers", [column])


def downgrade() -> None:
    for table in ("bloom_special_answers", "bloom_special_submissions", "bloom_special_options", "bloom_special_questions", "bloom_special_tasks", "bloom_garden_settings"):
        op.drop_table(table)
