from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_static_partner_token_can_manage_only_its_own_content() -> None:
    source = (ROOT / "app" / "api" / "v1" / "endpoints" / "partner_content.py").read_text(encoding="utf-8")

    assert 'router = APIRouter(prefix="/partner"' in source
    assert source.count("_require_partner_from_credentials(db, credentials)") >= 10
    assert "PartnerPhoto.partner_id == partner.id" in source
    assert "_get_owned_offer_or_404(db, partner.id, offer_id)" in source
    assert "offer.is_active = False" in source
    assert "is_active=False" in source


def test_partner_cabinet_exposes_card_gallery_and_service_management() -> None:
    source = (ROOT / "browser-mobile-app" / "src" / "PartnerPortalApp.tsx").read_text(encoding="utf-8")

    for marker in (
        "РџРѕРґС‚РІРµСЂРґРёС‚СЊ РїСЂРёРІРёР»РµРіРёСЋ",
        "РњРѕСЏ РєР°СЂС‚РѕС‡РєР°",
        "РЎРѕС…СЂР°РЅРёС‚СЊ РєР°СЂС‚РѕС‡РєСѓ",
        "Р”РѕР±Р°РІРёС‚СЊ С„РѕС‚Рѕ",
        "Р”РѕР±Р°РІРёС‚СЊ СѓСЃР»СѓРіСѓ",
        "РЎРѕС…СЂР°РЅРёС‚СЊ Рё РѕС‚РїСЂР°РІРёС‚СЊ РЅР° РїСЂРѕРІРµСЂРєСѓ",
        "РљР»РёРµРЅС‚ СѓРєР°Р·С‹РІР°РµС‚ СЃСѓРјРјСѓ Р·Р°РєР°Р·Р°",
        'partnerRequest<PartnerProfile>("/profile")',
        'partnerRequest<PartnerPhoto[]>("/photos")',
        'partnerRequest<PartnerOffer[]>("/offers")',
    ):
        assert marker in source


def test_partner_editor_keeps_mobile_safe_controls_and_moderation_statuses() -> None:
    styles = (ROOT / "browser-mobile-app" / "src" / "PartnerPortal.css").read_text(encoding="utf-8")
    source = (ROOT / "browser-mobile-app" / "src" / "PartnerPortalApp.tsx").read_text(encoding="utf-8")

    assert "env(safe-area-inset-top)" in styles
    assert "env(safe-area-inset-bottom)" in styles
    assert "font-size: 16px" in styles
    assert "min-height: 44px" in styles
    assert "РќР° РїСЂРѕРІРµСЂРєРµ" in source
    assert "РћРїСѓР±Р»РёРєРѕРІР°РЅРѕ" in source

