from __future__ import annotations

from pathlib import Path

NGINX_CONFIG = (Path(__file__).resolve().parents[1] / "ops" / "nginx" / "womenclub").read_text(encoding="utf-8")


def _server_block_for(server_name: str, *, ssl: bool = True) -> str:
    marker = f"server_name {server_name};"
    start = -1
    while True:
        start = NGINX_CONFIG.index(marker, start + 1)
        block_start = NGINX_CONFIG.rfind("server {", 0, start)
        next_block = NGINX_CONFIG.find("\nserver {", start)
        block = NGINX_CONFIG[block_start:] if next_block == -1 else NGINX_CONFIG[block_start:next_block]
        if ("listen 443 ssl" in block) is ssl:
            return block


def test_public_and_app_domains_do_not_share_any_server_name_block() -> None:
    public_marker = "server_name bloomclub.ru www.bloomclub.ru app.bloomclub.ru;"
    app_public_marker = "server_name app.bloomclub.ru bloomclub.ru www.bloomclub.ru;"

    assert public_marker not in NGINX_CONFIG
    assert app_public_marker not in NGINX_CONFIG


def test_http_redirect_server_blocks_are_separate_by_domain() -> None:
    public_block = _server_block_for("bloomclub.ru www.bloomclub.ru", ssl=False)
    app_block = _server_block_for("app.bloomclub.ru", ssl=False)

    assert "app.bloomclub.ru" not in public_block
    assert "bloomclub.ru www.bloomclub.ru" not in app_block
    assert "return 301 https://$host$request_uri;" in public_block
    assert "return 301 https://$host$request_uri;" in app_block


def test_public_domain_serves_public_frontend_dist_not_browser_mobile_app() -> None:
    block = _server_block_for("bloomclub.ru www.bloomclub.ru")

    assert "root /opt/fed_women_club_WEB/frontend/dist;" in block
    assert "browser-mobile-app/dist" not in block
    assert "try_files $uri $uri/ /index.html;" in block


def test_app_subdomain_serves_browser_mobile_app_dist() -> None:
    block = _server_block_for("app.bloomclub.ru")

    assert "root /opt/fed_women_club_WEB/browser-mobile-app/dist;" in block
    assert "root /opt/fed_women_club_WEB/frontend/dist;" not in block
    assert "try_files $uri $uri/ /index.html;" in block


def test_public_domain_does_not_expose_browser_login_code_endpoint() -> None:
    public_block = _server_block_for("bloomclub.ru www.bloomclub.ru")
    app_block = _server_block_for("app.bloomclub.ru")

    assert "location = /api/v1/auth/login-code" in public_block
    assert "return 404;" in public_block
    assert "location = /api/v1/auth/login-code" not in app_block


def test_public_domain_sets_baseline_security_headers() -> None:
    block = _server_block_for("bloomclub.ru www.bloomclub.ru")

    for header in (
        "Strict-Transport-Security",
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Referrer-Policy",
        "Permissions-Policy",
        "Content-Security-Policy",
    ):
        assert f"add_header {header}" in block
