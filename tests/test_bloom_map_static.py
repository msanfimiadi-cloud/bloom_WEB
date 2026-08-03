from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_bloom_map_uses_runtime_key_and_external_routes_without_hardcoded_secret() -> None:
    page = (ROOT / "browser-mobile-app/src/pages/BloomMapPage.tsx").read_text(encoding="utf-8")
    helpers = (ROOT / "browser-mobile-app/src/utils/bloomMap.ts").read_text(encoding="utf-8")
    runtime = (ROOT / "app/main.py").read_text(encoding="utf-8")

    assert 'fetch("/api/runtime-config"' in page
    assert "yandexMapsApiKey" in page
    assert "settings.YANDEX_MAPS_API_KEY" in runtime
    assert "https://yandex.ru/maps/?rtext=~" in helpers
    assert "https://2gis.ru/directions/points/|" in helpers
    assert "AIza" not in page


def test_bloom_map_is_publicly_reachable_from_catalog_and_graceful_without_coordinates() -> None:
    app = (ROOT / "browser-mobile-app/src/App.tsx").read_text(encoding="utf-8")
    catalog = (ROOT / "browser-mobile-app/src/pages/CatalogPage.tsx").read_text(encoding="utf-8")
    page = (ROOT / "browser-mobile-app/src/pages/BloomMapPage.tsx").read_text(encoding="utf-8")

    assert '| "map"' in app
    assert 'activePage === "map" && bloomMapEnabled' in app
    assert "Карта Bloom" in catalog
    assert "isBloomMapEnabled ?" in catalog
    assert 'fetch("/api/v1/public/bloom-map-settings"' in app
    assert "isBloomMapEnabled={bloomMapEnabled}" in app
    assert "getPartnerCoordinates(partner)" in page
    assert "В этой категории пока нет меток" in page

def test_bloom_map_admin_toggle_is_separate_and_persisted() -> None:
    source = (ROOT / "frontend/src/main.js").read_text(encoding="utf-8")
    model = (ROOT / "app/models/landing.py").read_text(encoding="utf-8")
    admin_api = (ROOT / "app/api/v1/endpoints/admin.py").read_text(encoding="utf-8")

    assert "{ id: 'bloomMap', label: 'Карта Bloom'" in source
    assert "data-admin-bloom-map-toggle" in source
    assert "/api/v1/admin/bloom-map-settings" in source
    assert "bloom_map_enabled" in model
    assert '@router.patch("/bloom-map-settings"' in admin_api


def test_yandex_runtime_failures_stay_inside_the_map_screen() -> None:
    entry = (ROOT / "browser-mobile-app/src/main.tsx").read_text(encoding="utf-8")
    boundary = (ROOT / "browser-mobile-app/src/components/RuntimeErrorBoundary.tsx").read_text(encoding="utf-8")
    page = (ROOT / "browser-mobile-app/src/pages/BloomMapPage.tsx").read_text(encoding="utf-8")
    helpers = (ROOT / "browser-mobile-app/src/utils/bloomMap.ts").read_text(encoding="utf-8")

    assert "isRecoverableYandexMapsError(event.reason)" in entry
    assert "isRecoverableYandexMapsError(event.reason)" in boundary
    assert "event.preventDefault()" in entry
    assert "coverage fetch failed" in helpers
    assert "BLOOM_MAP_RUNTIME_ERROR_EVENT" in page
    assert 'setStatus("error")' in page
