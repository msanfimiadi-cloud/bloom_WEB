from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "src"


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_cached_images_are_detected_without_waiting_for_a_new_load_event() -> None:
    component = read("components/AppImage.tsx")
    assert "image?.complete && image.naturalWidth > 0" in component
    assert "loadedSrc === safeSrc" in component


def test_page_changes_always_reset_scroll_position() -> None:
    app = read("App.tsx")
    assert "useEffect(() => {\n    scrollAppToTop();\n  }, [activePage]);" in app


def test_login_typing_does_not_recreate_resume_handlers_for_each_character() -> None:
    app = read("App.tsx")
    pending_guard = app[app.index("const hasPendingBrowserLoginDraft"):app.index("const preservePendingBrowserLoginFlow")]
    assert "telegramLoginCode" not in pending_guard
    assert "vkLoginCode" not in pending_guard
    assert "loginReferralCode" not in pending_guard
    assert "[browserLoginRequired]" in pending_guard


def test_privilege_history_uses_api_names_and_status_filters() -> None:
    page = read("pages/PrivilegesPage.tsx")
    assert "verification.partner_name" in page
    assert "verification.offer_title" in page
    assert "Активные" in page
    assert "Использованные" in page
    assert "Истёкшие" in page
    assert "Данные о стоимости для этого старого кода не были сохранены." in page


def test_rub_and_linked_account_are_rendered_for_people() -> None:
    savings = read("pages/SavingsPage.tsx")
    profile = read("pages/ProfilePage.tsx")
    assert "rawCurrency.toUpperCase() === 'RUB'" in savings
    assert "`Привязан${accountLabel ? `: ${accountLabel}` : \"\"}`" in profile
    assert "identity.linked_at" not in profile


def test_gallery_is_opaque_and_navigation_is_attached_to_frame() -> None:
    styles = read("styles.css")
    partner_page = read("pages/PartnerPage.tsx")
    assert "background: #181115 !important;" in styles
    frame = partner_page[partner_page.index('<div className="lightbox__frame">'):partner_page.index("return (", partner_page.index('<div className="lightbox__frame">'))]
    assert 'lightbox__nav--prev' in frame
    assert 'lightbox__nav--next' in frame
