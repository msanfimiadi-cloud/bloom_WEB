from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.acquiring import Payment, PaymentStatus
from app.services.payments import refresh_payment


async def main() -> int:
    if not settings.TOCHKA_PAYMENTS_ENABLED or not settings.TOCHKA_RECONCILIATION_ENABLED:
        print("OK: reconciliation disabled"); return 0
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.TOCHKA_RECONCILIATION_INTERVAL_MINUTES)
    with SessionLocal() as db:
        payments = db.execute(select(Payment).where(Payment.status.in_([PaymentStatus.created.value, PaymentStatus.pending.value, PaymentStatus.authorized.value]), Payment.provider_operation_id.is_not(None), Payment.fulfilled_at.is_(None), Payment.expired_at > datetime.now(timezone.utc), (Payment.last_synced_at.is_(None) | (Payment.last_synced_at < cutoff))).order_by(Payment.created_at).limit(100)).scalars().all()
        for payment in payments:
            try: await refresh_payment(db, payment, source="background_sync")
            except Exception as exc: print(f"WARNING: {payment.public_id}: {type(exc).__name__}")
        print(f"OK: reconciled {len(payments)} payments")
    return 0


if __name__ == "__main__": raise SystemExit(asyncio.run(main()))
