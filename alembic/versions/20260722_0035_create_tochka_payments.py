"""create Tochka acquiring payments

Revision ID: 20260722_0035
Revises: 20260722_0034
"""

from alembic import op
import sqlalchemy as sa


revision = "20260722_0035"
down_revision = "20260722_0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(140), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="RUB"),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.bulk_insert(
        sa.table(
            "subscription_plans",
            sa.column("id", sa.Integer()), sa.column("code", sa.String()), sa.column("name", sa.String()),
            sa.column("price", sa.Numeric()), sa.column("currency", sa.String()),
            sa.column("duration_days", sa.Integer()), sa.column("is_active", sa.Boolean()),
        ),
        [{"id": 1, "code": "monthly", "name": "Подписка Bloom Club на 30 дней", "price": 349.00, "currency": "RUB", "duration_days": 30, "is_active": True}],
    )
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("client_profile_id", sa.Integer(), sa.ForeignKey("client_profiles.id"), nullable=False),
        sa.Column("subscription_plan_id", sa.Integer(), sa.ForeignKey("subscription_plans.id"), nullable=False),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id"), nullable=True),
        sa.Column("provider", sa.String(32), nullable=False, server_default="tochka"),
        sa.Column("provider_operation_id", sa.String(128), nullable=True),
        sa.Column("payment_link_id", sa.String(45), nullable=False),
        sa.Column("provider_payment_url", sa.Text(), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="RUB"),
        sa.Column("purpose", sa.String(140), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="created"),
        sa.Column("provider_status", sa.String(64), nullable=True),
        sa.Column("payment_method", sa.String(32), nullable=True),
        sa.Column("payment_modes", sa.JSON(), nullable=False),
        sa.Column("payment_type", sa.String(32), nullable=False, server_default="subscription"),
        sa.Column("recurring", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("subscription_provider_id", sa.String(128), nullable=True),
        sa.Column("customer_code", sa.String(64), nullable=False),
        sa.Column("merchant_id", sa.String(64), nullable=False),
        sa.Column("terminal_id", sa.String(64), nullable=True),
        sa.Column("receipt_email", sa.String(320), nullable=False),
        sa.Column("receipt_phone", sa.String(32), nullable=True),
        sa.Column("provider_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("authorized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refunded_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("failure_code", sa.String(128), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("public_id", name="uq_payments_public_id"),
        sa.UniqueConstraint("provider", "provider_operation_id", name="uq_payments_provider_operation"),
        sa.UniqueConstraint("provider", "payment_link_id", name="uq_payments_provider_link"),
    )
    for name, column in (("user_id", "user_id"), ("client_profile_id", "client_profile_id"), ("status", "status"), ("created_at", "created_at"), ("paid_at", "paid_at")):
        op.create_index(f"ix_payments_{name}", "payments", [column])
    op.create_table(
        "payment_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("payment_id", sa.Integer(), sa.ForeignKey("payments.id", ondelete="CASCADE"), nullable=True),
        sa.Column("provider", sa.String(32), nullable=False, server_default="tochka"),
        sa.Column("event_type", sa.String(96), nullable=False),
        sa.Column("provider_event_id", sa.String(160), nullable=False),
        sa.Column("provider_status", sa.String(64), nullable=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("signature_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("raw_body_hash", sa.String(64), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("processing_status", sa.String(32), nullable=False, server_default="received"),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("provider", "provider_event_id", name="uq_payment_events_provider_event"),
    )
    op.create_index("ix_payment_events_payment_id", "payment_events", ["payment_id"])
    op.create_index("ix_payment_events_received_at", "payment_events", ["received_at"])
    op.create_table(
        "payment_refunds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("payment_id", sa.Integer(), sa.ForeignKey("payments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("public_id", sa.String(36), nullable=False, unique=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("provider_refund_id", sa.String(128), nullable=True),
        sa.Column("requested_by_admin_id", sa.Integer(), sa.ForeignKey("admin_users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_payment_refunds_payment_id", "payment_refunds", ["payment_id"])


def downgrade() -> None:
    op.drop_index("ix_payment_refunds_payment_id", table_name="payment_refunds")
    op.drop_table("payment_refunds")
    op.drop_index("ix_payment_events_received_at", table_name="payment_events")
    op.drop_index("ix_payment_events_payment_id", table_name="payment_events")
    op.drop_table("payment_events")
    for name in ("paid_at", "created_at", "status", "client_profile_id", "user_id"):
        op.drop_index(f"ix_payments_{name}", table_name="payments")
    op.drop_table("payments")
    op.drop_table("subscription_plans")
