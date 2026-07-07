#!/usr/bin/env python3
"""Staging checks for legacy WEB content admin read-only rollout.

Safe by default: performs health/auth/read checks only. The optional
--include-write-checks mode sends a non-destructive PATCH {} to a legacy WEB
content endpoint and expects it to be blocked with 403 when
WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED=false.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    status: int | None
    expected: str
    detail: str = ""


def _base_url() -> str:
    return os.getenv("BASE_URL", "https://bloomclub.ru").rstrip("/") + "/"


def _request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    body: dict[str, Any] | None = None,
) -> tuple[int | None, str]:
    headers = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = Request(
        urljoin(_base_url(), path.lstrip("/")),
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(request, timeout=20) as response:  # nosec B310: operational URL is operator-provided.
            return response.status, response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except URLError as exc:
        return None, str(exc.reason)
    except TimeoutError as exc:
        return None, str(exc)


def _json_field(raw: str, field: str) -> Any:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return payload.get(field) if isinstance(payload, dict) else None


def _result(name: str, status: int | None, expected_status: int, body: str = "") -> CheckResult:
    return CheckResult(
        name=name,
        ok=status == expected_status,
        status=status,
        expected=f"HTTP {expected_status}",
        detail=body[:300].replace("\n", " "),
    )


def run_checks(include_write_checks: bool) -> list[CheckResult]:
    admin_token = os.getenv("ADMIN_TOKEN") or os.getenv("ADMIN_JWT")
    telegram_token = os.getenv("TELEGRAM_ADMIN_API_TOKEN")
    results: list[CheckResult] = []

    status, body = _request("GET", "/api/content/health")
    results.append(_result("content health", status, 200, body))

    if admin_token:
        status, body = _request("GET", "/api/v1/admin/me", token=admin_token)
        flag = _json_field(body, "legacy_content_write_enabled")
        results.append(
            CheckResult(
                name="admin/me exposes legacy_content_write_enabled=false",
                ok=status == 200 and flag is False,
                status=status,
                expected="HTTP 200 and legacy_content_write_enabled=false",
                detail=f"legacy_content_write_enabled={flag!r}",
            )
        )
    else:
        results.append(
            CheckResult(
                name="admin/me exposes legacy_content_write_enabled=false",
                ok=False,
                status=None,
                expected="ADMIN_TOKEN or ADMIN_JWT env is set",
                detail="skipped: missing WEB admin JWT",
            )
        )

    if telegram_token:
        status, body = _request(
            "GET", "/api/content/admin/cities", token=telegram_token
        )
        results.append(_result("content admin cities with valid token", status, 200, body))
    else:
        results.append(
            CheckResult(
                name="content admin cities with valid token",
                ok=False,
                status=None,
                expected="TELEGRAM_ADMIN_API_TOKEN env is set",
                detail="skipped: missing Telegram admin token",
            )
        )

    status, body = _request("GET", "/api/content/admin/cities")
    results.append(_result("content admin cities without token", status, 401, body))

    status, body = _request(
        "GET", "/api/content/admin/cities", token="definitely-wrong-token"
    )
    results.append(_result("content admin cities with wrong token", status, 403, body))

    if include_write_checks:
        if admin_token:
            status, body = _request(
                "PATCH",
                "/api/v1/admin/landing-settings",
                token=admin_token,
                body={},
            )
            results.append(_result("legacy WEB content write is blocked", status, 403, body))
        else:
            results.append(
                CheckResult(
                    name="legacy WEB content write is blocked",
                    ok=False,
                    status=None,
                    expected="ADMIN_TOKEN or ADMIN_JWT env is set",
                    detail="skipped: missing WEB admin JWT",
                )
            )

    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check staging readiness for WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED=false."
    )
    parser.add_argument(
        "--include-write-checks",
        action="store_true",
        help="also send a non-destructive legacy WEB PATCH {} and expect 403",
    )
    args = parser.parse_args()

    print(f"BASE_URL={_base_url().rstrip('/')}")
    if not args.include_write_checks:
        print("write checks: skipped (pass --include-write-checks to enable)")

    results = run_checks(include_write_checks=args.include_write_checks)
    for item in results:
        marker = "PASS" if item.ok else "FAIL"
        status = item.status if item.status is not None else "n/a"
        print(f"[{marker}] {item.name}: got {status}; expected {item.expected}")
        if item.detail:
            print(f"       {item.detail}")

    failed = [item for item in results if not item.ok]
    if failed:
        print(f"\n{len(failed)} check(s) failed.")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
