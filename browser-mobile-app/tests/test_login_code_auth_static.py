from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "src" / "App.tsx").read_text(encoding="utf-8")
CLIENT = (ROOT / "src" / "api" / "client.ts").read_text(encoding="utf-8")


def test_browser_app_uses_login_code_endpoint_not_browser_token_endpoint() -> None:
    assert 'LOGIN_CODE_PATH = "/api/v1/auth/login-code"' in CLIENT
    assert "loginWithCode" in CLIENT
    assert "browserTokenLogin" not in APP
    assert "BROWSER_TOKEN_LOGIN_PATH" not in CLIENT


def test_browser_startup_shows_welcome_and_login_code_guest_choices() -> None:
    assert "Добро пожаловать в Bloom Club" in APP
    assert "Войти по коду" in APP
    assert "Продолжить без регистрации" in APP


def test_guest_registration_modal_blocks_protected_actions() -> None:
    assert "Требуется регистрация" in APP
    assert "Чтобы воспользоваться возможностями Bloom Club" in APP
    assert "Ввести код" in APP
    assert "Позже" in APP
    assert "requireRegisteredUser" in APP


def test_empty_telegram_webapp_init_data_falls_back_to_login_code_welcome() -> None:
    bootstrap_section = APP[APP.index('const loginWithTelegramPayload'):APP.index('let profile: ClientProfile;')]
    assert 'const hasValidInitData = hasValidTelegramMiniAppInitData(' in bootstrap_section
    assert 'if (!hasValidInitData)' in bootstrap_section
    assert 'empty_init_data_browser_app' in bootstrap_section
    assert 'return false;' in bootstrap_section
    assert 'Telegram WebApp доступен, но Telegram не передал launch payload' not in bootstrap_section
    assert 'Telegram WebApp SDK не найден' not in bootstrap_section


def test_no_jwt_empty_init_data_shows_login_code_for_desktop_iphone_and_telegram_browser() -> None:
    startup_section = APP[APP.index('if (storedAuthToken && !forceNewIdentity)'):APP.index('traceMark("auth_finished"')]
    assert 'if (!(await loginWithTelegramPayload()))' in startup_section
    assert 'setBrowserLoginRequired(!browserGuestMode);' in startup_section
    assert 'setIsBootstrapDone(true);' in startup_section
    assert 'Войти по коду' in APP
    assert 'Продолжить без регистрации' in APP


def test_valid_telegram_init_data_runs_mini_app_login_flow() -> None:
    webapp = (ROOT / "src" / "telegram" / "webapp.ts").read_text(encoding="utf-8")
    bootstrap_section = APP[APP.index('const loginWithTelegramPayload'):APP.index('let profile: ClientProfile;')]
    assert 'export function hasValidTelegramMiniAppInitData' in webapp
    assert 'params.get("hash")' in webapp
    assert 'params.get("auth_date")' in webapp
    assert 'params.get("user") || params.get("query_id")' in webapp
    assert 'loginWithTelegram(telegramLaunchPayload' in bootstrap_section
    assert 'return true;' in bootstrap_section


def test_stored_jwt_loads_authenticated_app_before_telegram_init_data_check() -> None:
    startup_section = APP[APP.index('const storedAuthToken = authSnapshot.token;'):APP.index('} else {', APP.index('if (storedAuthToken && !forceNewIdentity)'))]
    assert 'await requestProfileAndSubscription()' in startup_section
    assert 'await loginWithTelegramPayload()' not in startup_section.split('} catch (caughtError)')[0]
