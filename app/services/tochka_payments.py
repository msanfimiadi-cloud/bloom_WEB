from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Mapping
from typing import Any
from uuid import uuid4

import httpx
from jose import JWTError, jwk, jwt

from app.core.config import settings
from app.schemas.acquiring import ProviderResult, TochkaWebhookPayload


logger = logging.getLogger("app.payments.tochka")


class TochkaError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, error_code: str | None = None, request_id: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.request_id = request_id


class TochkaAuthenticationError(TochkaError): pass
class TochkaPermissionError(TochkaError): pass
class TochkaValidationError(TochkaError): pass
class TochkaNotFoundError(TochkaError): pass
class TochkaRateLimitError(TochkaError): pass
class TochkaTemporaryError(TochkaError): pass
class TochkaInvalidResponseError(TochkaError): pass
class TochkaPaymentConflictError(TochkaError): pass
class TochkaWebhookSignatureError(TochkaError): pass


def _data(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    value: Any = payload
    for key in ("Data", "data"):
        if isinstance(value, Mapping) and isinstance(value.get(key), Mapping):
            value = value[key]
            break
    return value if isinstance(value, Mapping) else payload


def _first(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return value
    return None


class TochkaPaymentsClient:
    def __init__(self, client: httpx.AsyncClient | None = None):
        token = settings.TOCHKA_JWT_TOKEN.get_secret_value()
        if not token:
            raise TochkaAuthenticationError("Tochka JWT is not configured")
        timeout = httpx.Timeout(settings.TOCHKA_REQUEST_TIMEOUT_SECONDS, connect=min(5, settings.TOCHKA_REQUEST_TIMEOUT_SECONDS))
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            base_url=settings.TOCHKA_API_BASE_URL.rstrip("/"),
            timeout=timeout,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json", "Content-Type": "application/json"},
        )

    async def __aenter__(self): return self

    async def __aexit__(self, *_):
        if self._owns_client:
            await self.client.aclose()

    async def _request(self, method: str, path: str, *, json_body: dict | None = None, params: dict | None = None, retry_safe: bool = False) -> dict:
        request_id = str(uuid4())
        attempts = 3 if retry_safe else 1
        for attempt in range(attempts):
            started = time.perf_counter()
            try:
                response = await self.client.request(method, path, json=json_body, params=params, headers={"X-Request-ID": request_id})
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if retry_safe and attempt + 1 < attempts:
                    await asyncio.sleep(0.25 * (2 ** attempt))
                    continue
                raise TochkaTemporaryError("Tochka request outcome is unknown", request_id=request_id) from exc
            logger.info("tochka_api method=%s path=%s status=%s duration_ms=%.2f request_id=%s", method, path, response.status_code, (time.perf_counter() - started) * 1000, request_id)
            if response.status_code in {429, 500, 502, 503, 504} and retry_safe and attempt + 1 < attempts:
                await asyncio.sleep(0.25 * (2 ** attempt))
                continue
            if response.status_code >= 400:
                self._raise_response_error(response, request_id)
            try:
                payload = response.json()
            except ValueError as exc:
                raise TochkaInvalidResponseError("Tochka returned invalid JSON", status_code=response.status_code, request_id=request_id) from exc
            if not isinstance(payload, dict):
                raise TochkaInvalidResponseError("Tochka returned an unexpected response", status_code=response.status_code, request_id=request_id)
            return payload
        raise TochkaTemporaryError("Tochka is temporarily unavailable", request_id=request_id)

    @staticmethod
    def _raise_response_error(response: httpx.Response, request_id: str) -> None:
        try:
            body = response.json()
        except ValueError:
            body = {}
        code = str(_first(body if isinstance(body, dict) else {}, "code", "errorCode", "error") or "")[:128] or None
        kwargs = {"status_code": response.status_code, "error_code": code, "request_id": request_id}
        if response.status_code == 401:
            raise TochkaAuthenticationError("Tochka JWT is invalid or expired", **kwargs)
        if response.status_code == 403:
            raise TochkaPermissionError("Tochka JWT lacks required permissions", **kwargs)
        if response.status_code == 404:
            raise TochkaNotFoundError("Tochka operation was not found", **kwargs)
        if response.status_code == 429:
            raise TochkaRateLimitError("Tochka rate limit exceeded", **kwargs)
        if response.status_code in {400, 422}:
            raise TochkaValidationError("Tochka rejected request data", **kwargs)
        if response.status_code == 409:
            raise TochkaPaymentConflictError("Tochka payment conflict", **kwargs)
        raise TochkaTemporaryError("Tochka is temporarily unavailable", **kwargs)

    async def get_customers(self) -> dict:
        return await self._request("GET", "/open-banking/v1.0/customers", retry_safe=True)

    async def get_retailers(self, customer_code: str | None = None) -> dict:
        params = {"customerCode": customer_code or settings.TOCHKA_CUSTOMER_CODE}
        return await self._request("GET", "/acquiring/v1.0/retailers", params=params, retry_safe=True)

    async def create_payment_with_receipt(self, data: dict) -> ProviderResult:
        payload = await self._request("POST", "/acquiring/v1.0/payments_with_receipt", json_body={"Data": data})
        body = _data(payload)
        operation_id = _first(body, "operationId", "operation_id")
        payment_url = _first(body, "paymentLink", "paymentUrl", "paymentURL", "url")
        if not operation_id or not payment_url:
            raise TochkaInvalidResponseError("Tochka response has no operationId or payment link")
        return ProviderResult(operation_id=str(operation_id), payment_url=str(payment_url), status=_first(body, "status"), payment_link_id=_first(body, "paymentLinkId"), raw=payload)

    async def get_payment_info(self, operation_id: str) -> dict:
        return await self._request("GET", f"/acquiring/v1.0/payments/{operation_id}", retry_safe=True)

    async def get_payment_list(self, *, from_date: str, to_date: str) -> dict:
        return await self._request("GET", "/acquiring/v1.0/payments", params={"customerCode": settings.TOCHKA_CUSTOMER_CODE, "fromDate": from_date, "toDate": to_date}, retry_safe=True)

    async def refund_payment(self, operation_id: str, amount: str) -> dict:
        return await self._request("POST", f"/acquiring/v1.0/payments/{operation_id}/refund", json_body={"Data": {"amount": amount}})

    async def get_payment_registry(self, date: str) -> dict:
        return await self._request("GET", "/acquiring/v1.0/payments_registry", params={"customerCode": settings.TOCHKA_CUSTOMER_CODE, "merchantId": settings.TOCHKA_MERCHANT_ID, "date": date}, retry_safe=True)

    async def get_webhooks(self) -> dict:
        return await self._request("GET", f"/webhook/v1.0/{settings.TOCHKA_CLIENT_ID}", retry_safe=True)

    async def create_webhook(self, url: str, webhook_type: str = "acquiringInternetPayment") -> dict:
        return await self._request("POST", f"/webhook/v1.0/{settings.TOCHKA_CLIENT_ID}", json_body={"Data": {"url": url, "webhooksList": [webhook_type]}})

    async def edit_webhook(self, webhook_id: str, url: str, webhook_type: str = "acquiringInternetPayment") -> dict:
        return await self._request("PUT", f"/webhook/v1.0/{settings.TOCHKA_CLIENT_ID}/{webhook_id}", json_body={"Data": {"url": url, "webhooksList": [webhook_type]}})

    async def delete_webhook(self, webhook_id: str) -> dict:
        return await self._request("DELETE", f"/webhook/v1.0/{settings.TOCHKA_CLIENT_ID}/{webhook_id}")

    async def send_test_webhook(self) -> dict:
        return await self._request("POST", f"/webhook/v1.0/{settings.TOCHKA_CLIENT_ID}/test/send", json_body={"Data": {"webhookType": "acquiringInternetPayment"}})


def verify_webhook(raw_token: str) -> TochkaWebhookPayload:
    try:
        header = jwt.get_unverified_header(raw_token)
    except JWTError as exc:
        raise TochkaWebhookSignatureError("Invalid webhook token") from exc
    if header.get("alg") != "RS256":
        raise TochkaWebhookSignatureError("Unsupported webhook algorithm")
    raw_key = settings.TOCHKA_WEBHOOK_PUBLIC_KEY.get_secret_value().strip()
    if not raw_key:
        raise TochkaWebhookSignatureError("Webhook public key is not configured")
    try:
        key: Any = raw_key
        if raw_key.startswith("{"):
            key = jwk.construct(json.loads(raw_key), algorithm="RS256").to_pem().decode()
        payload = jwt.decode(raw_token, key, algorithms=["RS256"], options={"verify_aud": False})
        return TochkaWebhookPayload.model_validate(payload)
    except (JWTError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise TochkaWebhookSignatureError("Invalid webhook signature or payload") from exc
