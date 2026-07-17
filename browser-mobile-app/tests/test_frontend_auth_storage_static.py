from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "src/api/client.ts"


def test_auth_token_persisted_to_local_and_session_storage_for_browser_resume() -> None:
    source = CLIENT.read_text(encoding="utf-8")
    assert 'export const AUTH_STORAGE_KEY = "bloom_club_tma_auth"' in source
    assert 'const AUTH_SESSION_STORAGE_KEY = "bloom_club_tma_auth_session"' in source
    assert 'window.localStorage.setItem(AUTH_STORAGE_KEY, token)' in source
    assert 'window.sessionStorage.setItem(' in source
    assert 'JSON.stringify({ token, expiresAt, storedAt: Date.now() })' in source


def test_auth_session_reads_snapshot_with_persistent_storage_before_session_fallback() -> None:
    source = CLIENT.read_text(encoding="utf-8")
    snapshot = source[source.index('export function getAuthTokenStorageSnapshot'):source.index('export function getStoredAuthToken')]
    assert 'window.localStorage.getItem(AUTH_STORAGE_KEY)' in snapshot
    assert 'const sessionToken = readSessionAuthToken(now);' in snapshot
    assert 'window.sessionStorage.getItem(AUTH_SESSION_STORAGE_KEY)' in source
    assert snapshot.index('window.localStorage.getItem(AUTH_STORAGE_KEY)') < snapshot.index('readSessionAuthToken(now)')
    assert 'tokenSource: "local"' in snapshot
