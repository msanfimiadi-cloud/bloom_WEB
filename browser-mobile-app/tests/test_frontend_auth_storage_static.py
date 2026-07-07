from pathlib import Path

CLIENT = Path(__file__).resolve().parents[1] / "src" / "api" / "client.ts"


def test_auth_token_persisted_to_local_storage_for_browser_resume() -> None:
    source = CLIENT.read_text()

    assert 'export const AUTH_STORAGE_KEY = "bloom_club_tma_auth"' in source
    assert 'const AUTH_SESSION_STORAGE_KEY = "bloom_club_tma_auth_session"' in source
    assert 'window.localStorage.setItem(AUTH_STORAGE_KEY, token)' in source
    assert 'window.sessionStorage.setItem(\n    AUTH_SESSION_STORAGE_KEY' in source


def test_auth_session_reads_persistent_local_storage_before_session_fallback() -> None:
    source = CLIENT.read_text()
    get_stored = source[source.index('export function getStoredAuthToken'):source.index('export function clearStoredAuthToken')]

    assert 'const AUTH_SESSION_TTL_MS = 30 * 60 * 1000' in source
    assert 'const AUTH_SESSION_MAX_TTL_MS = 30 * 24 * 60 * 60 * 1000' in source
    assert 'window.localStorage.getItem(AUTH_STORAGE_KEY)' in get_stored
    assert get_stored.index('window.localStorage.getItem(AUTH_STORAGE_KEY)') < get_stored.index('return readSessionAuthToken(now);')
