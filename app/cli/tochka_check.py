from __future__ import annotations

import asyncio

from app.core.config import settings
from app.services.tochka_payments import TochkaPaymentsClient


def rows(value):
    if isinstance(value, list): return value
    if not isinstance(value, dict): return []
    data = value.get("Data") or value.get("data") or value
    if isinstance(data, list): return data
    if isinstance(data, dict):
        for key in ("customers", "Customers", "retailers", "Retailers", "webhooks", "Webhooks"):
            if isinstance(data.get(key), list): return data[key]
    return []


def out(level: str, message: str): print(f"{level}: {message}")


async def main() -> int:
    if not settings.TOCHKA_JWT_TOKEN.get_secret_value(): out("ERROR", "JWT не задан"); return 1
    try:
        async with TochkaPaymentsClient() as client:
            customers = rows(await client.get_customers())
            out("OK", "API доступно, Get Customers List работает")
            business = next((x for x in customers if x.get("customerType") == "Business"), None)
            if not business: out("ERROR", "customerCode типа Business не найден"); return 1
            customer_code = business.get("customerCode")
            out("OK", f"customerCode найден: …{str(customer_code)[-4:]}")
            retailers = rows(await client.get_retailers(str(customer_code)))
            retailer = next((x for x in retailers if x.get("status") == "REG" and x.get("isActive") is True), None)
            if not retailer: out("ERROR", "Активная торговая точка REG не найдена"); return 1
            out("OK", "торговая точка REG и активна")
            out("OK" if retailer.get("merchantId") else "ERROR", "merchantId найден" if retailer.get("merchantId") else "merchantId отсутствует")
            out("OK" if retailer.get("terminalId") else "ERROR", "terminalId найден" if retailer.get("terminalId") else "terminalId отсутствует")
            modes = retailer.get("paymentModes") or []
            out("OK" if "sbp" in modes else "ERROR", "СБП доступен" if "sbp" in modes else "СБП недоступен")
            out("OK" if "card" in modes else "WARNING", "карта доступна" if "card" in modes else "карта недоступна")
            out("OK" if retailer.get("cashbox") else "WARNING", "касса подключена" if retailer.get("cashbox") else "касса не подтверждена")
            hooks = rows(await client.get_webhooks())
            registered = any((x.get("url") == settings.TOCHKA_WEBHOOK_URL and "acquiringInternetPayment" in (x.get("webhooksList") or x.get("webhookTypes") or [])) for x in hooks)
            out("OK" if registered else "WARNING", "webhook зарегистрирован" if registered else "webhook не найден")
            return 0
    except Exception as exc:
        out("ERROR", f"{type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__": raise SystemExit(asyncio.run(main()))
