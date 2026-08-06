from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "frontend" / "src" / "main.js").read_text(encoding="utf-8")
STYLES = (ROOT / "frontend" / "src" / "styles.css").read_text(encoding="utf-8")


def test_partner_gallery_photos_have_visible_delete_controls() -> None:
    assert 'class="partner-photo-delete-overlay ui-button ui-button--danger"' in MAIN
    assert 'data-partner-photo-delete="${escapeHtml(photo.id)}"' in MAIN
    assert 'aria-label="Удалить фото из галереи"' in MAIN
    assert "await deletePartnerPhoto(partnerPhotoDelete.dataset.partnerPhotoDelete)" in MAIN


def test_partner_offer_photos_have_visible_delete_controls() -> None:
    assert 'data-partner-offer-photo-delete="${escapeHtml(photo.id)}"' in MAIN
    assert 'aria-label="Удалить фото услуги"' in MAIN
    assert "await deletePartnerOfferPhoto(" in MAIN


def test_partner_photo_delete_control_is_overlaid_on_the_photo() -> None:
    assert ".partner-gallery-card {\n  position: relative;" in STYLES
    assert ".partner-photo-delete-overlay {" in STYLES
    delete_rule = STYLES.split(".partner-photo-delete-overlay {", 1)[1].split("}", 1)[0]
    assert "position: absolute" in delete_rule
    assert "z-index: 5" in delete_rule
