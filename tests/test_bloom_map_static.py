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
    assert 'activePage === "map"' in app
    assert "Карта Bloom" in catalog
    assert "getPartnerCoordinates(partner)" in page
    assert "В этой категории пока нет меток" in page

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
