from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_partner_portal_contains_required_confirmation_flow() -> None:
    source = (ROOT / "browser-mobile-app" / "src" / "PartnerPortalApp.tsx").read_text(encoding="utf-8")

    for marker in (
        'bloom.partnerAccessToken',
        '"/code-login"',
        'Подтвердить привилегию',
        'Введите код клиента',
        'Сумма без экономии',
        'Сумма с экономией',
        'Экономия клиентки',
        'finishPrivilege("confirm")',
        'finishPrivilege("reject")',
        'клиентов пришло',
        'привилегий использовано',
    ):
        assert marker in source


def test_partner_portal_is_routed_separately_from_client_app() -> None:
    entry = (ROOT / "browser-mobile-app" / "src" / "main.tsx").read_text(encoding="utf-8")
    client_app = (ROOT / "browser-mobile-app" / "src" / "App.tsx").read_text(encoding="utf-8")

    assert 'window.location.pathname === "/partner"' in entry
    assert 'import("./PartnerPortalApp")' in entry
    assert 'href="/partner"' in client_app
    assert 'Вход для партнёров' in client_app


def test_partner_portal_keeps_primary_action_visible_and_mobile_safe() -> None:
    styles = (ROOT / "browser-mobile-app" / "src" / "styles.css").read_text(encoding="utf-8")

    for marker in (
        '.partner-confirm-hero__button',
        'min-height: 64px',
        'env(safe-area-inset-top)',
        'env(safe-area-inset-bottom)',
        'font-size: 16px',
    ):
        assert marker in styles
