from __future__ import annotations

import argparse
import asyncio

from app.cli.tochka_check import rows
from app.core.config import settings
from app.services.tochka_payments import TochkaPaymentsClient


async def run(command: str) -> int:
    async with TochkaPaymentsClient() as client:
        hooks = rows(await client.get_webhooks())
        if command == "list":
            for hook in hooks: print({"id": hook.get("id") or hook.get("webhookId"), "url": hook.get("url"), "events": hook.get("webhooksList") or hook.get("webhookTypes")})
            return 0
        if command == "test":
            await client.send_test_webhook(); print("OK: test webhook requested"); return 0
        matching = [x for x in hooks if x.get("url") == settings.TOCHKA_WEBHOOK_URL and "acquiringInternetPayment" in (x.get("webhooksList") or x.get("webhookTypes") or [])]
        if matching: print("OK: webhook already configured"); return 0
        same_event = next((x for x in hooks if "acquiringInternetPayment" in (x.get("webhooksList") or x.get("webhookTypes") or [])), None)
        if same_event:
            webhook_id = same_event.get("id") or same_event.get("webhookId")
            if webhook_id:
                await client.edit_webhook(str(webhook_id), settings.TOCHKA_WEBHOOK_URL)
                print("OK: webhook updated")
                return 0
        await client.create_webhook(settings.TOCHKA_WEBHOOK_URL)
        print("OK: webhook created")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("ensure", "list", "test"))
    return asyncio.run(run(parser.parse_args().command))


if __name__ == "__main__": raise SystemExit(main())
