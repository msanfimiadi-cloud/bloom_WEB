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
        "Подтвердить привилегию",
        "Моя карточка",
        "Сохранить карточку",
        "Добавить фото",
        "Добавить услугу",
        "Сохранить и отправить на проверку",
        "Клиент указывает сумму заказа",
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
    assert "На проверке" in source
    assert "Опубликовано" in source

