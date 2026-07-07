from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTNER_DISPLAY = (ROOT / "src" / "utils" / "partnerDisplay.ts").read_text(encoding="utf-8")
CATALOG_PAGE = (ROOT / "src" / "pages" / "CatalogPage.tsx").read_text(encoding="utf-8")
HOME_PAGE = (ROOT / "src" / "pages" / "HomePage.tsx").read_text(encoding="utf-8")
PARTNER_PAGE = (ROOT / "src" / "pages" / "PartnerPage.tsx").read_text(encoding="utf-8")


def test_partner_catalog_maps_backend_image_fields_correctly() -> None:
    image_section = PARTNER_DISPLAY[PARTNER_DISPLAY.index("export function getPartnerImages"):PARTNER_DISPLAY.index("export function getOfferImages")]
    for field in ["image_url", "photo_url", "logo_url", "cover_url", "avatar_url", "photos", "images", "gallery", "media"]:
        assert field in image_section
    collect_section = PARTNER_DISPLAY[PARTNER_DISPLAY.index("function collectMediaValues"):PARTNER_DISPLAY.index("export function getPartnerName")]
    for field in ["image_url", "photo_url", "logo_url", "url", "src", "path", "file_path"]:
        assert f"field(value, '{field}')" in collect_section


def test_relative_partner_image_urls_are_normalized_to_current_origin() -> None:
    normalize_section = PARTNER_DISPLAY[PARTNER_DISPLAY.index("function normalizePartnerMediaUrlForDisplay"):PARTNER_DISPLAY.index("function collectMediaValues")]
    assert "getMediaOrigin()" in normalize_section
    assert "`${getMediaOrigin()}${text}`" in normalize_section
    assert "`${getMediaOrigin()}/${text}`" in normalize_section
    assert "return text;" in normalize_section


def test_partner_image_render_uses_normalized_image_url() -> None:
    assert "const image = getPartnerImage(partner);" in CATALOG_PAGE
    assert "<PartnerCardImage src={image} name={name} partner={partner} />" in CATALOG_PAGE
    assert "const image = getPartnerImage(partner);" in HOME_PAGE
    assert "<AppImage src={image}" in HOME_PAGE
    assert "const images = getPartnerImages(currentPartner)" in PARTNER_PAGE
    assert "<SmoothImage className=\"partner-detail__image\" src={images[0]}" in PARTNER_PAGE


def test_app_bloomclub_relative_image_urls_are_not_rewritten_to_legacy_web_origin() -> None:
    normalize_section = PARTNER_DISPLAY[PARTNER_DISPLAY.index("function normalizePartnerMediaUrlForDisplay"):PARTNER_DISPLAY.index("function collectMediaValues")]
    assert "SITE_ORIGIN" not in normalize_section
    assert "window.location.origin" in PARTNER_DISPLAY
    assert "https://bloomclub.ru${text}" not in PARTNER_DISPLAY


def test_partner_image_diagnostics_are_dev_or_debug_only() -> None:
    assert "import.meta.env.DEV" in PARTNER_DISPLAY
    assert "import.meta.env.MODE === 'test'" in PARTNER_DISPLAY
    assert "localStorage.getItem('BLOOM_DEBUG')" in PARTNER_DISPLAY
    assert "partner_image_diagnostic" in PARTNER_DISPLAY
    assert "tracePartnerImageDiagnostic(\"catalog_card_image_mapped\"" in CATALOG_PAGE
    assert "tracePartnerImageDiagnostic(\"image_load_error\"" in CATALOG_PAGE


def test_realistic_catalog_photo_url_has_priority_over_cover_and_logo() -> None:
    image_section = PARTNER_DISPLAY[PARTNER_DISPLAY.index("export function getPartnerImages"):PARTNER_DISPLAY.index("export function getOfferImages")]
    assert image_section.index("partner.photos") < image_section.index("partner.photo_url") < image_section.index("partner.image_url")
    assert image_section.index("partner.photo_url") < image_section.index("partner.cover_url") < image_section.index("partner.logo_url")


def test_schastye_est_style_catalog_object_uses_backend_image_url_alias() -> None:
    image_section = PARTNER_DISPLAY[PARTNER_DISPLAY.index("export function getPartnerImages"):PARTNER_DISPLAY.index("export function getOfferImages")]
    assert "partner.image_url" in image_section
    assert "image_url?: BackendText" in (ROOT / "src" / "api" / "types.ts").read_text(encoding="utf-8")


def test_image_diagnostics_include_selected_candidate_and_raw_media_fields() -> None:
    diagnostic_section = PARTNER_DISPLAY[PARTNER_DISPLAY.index("export function tracePartnerImageDiagnostic"):PARTNER_DISPLAY.index("export interface OfferPrices")]
    assert "selectedImageCandidate" in diagnostic_section
    for field in ["partnerId", "partnerName", "rawImageFields", "photo_url", "photos", "cover_url", "logo_url"]:
        assert field in diagnostic_section
