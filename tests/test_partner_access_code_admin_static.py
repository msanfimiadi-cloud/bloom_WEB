from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_JS = ROOT / "frontend" / "src" / "main.js"


def test_partner_access_tab_has_dedicated_static_code_flow() -> None:
    source = MAIN_JS.read_text(encoding="utf-8")

    for marker in (
        'data-admin-form="partnerCode"',
        'Коды для кабинета партнёра',
        'Выдать код для входа',
        'data-partner-code-generate',
        'data-partner-code-copy',
        "generatePartnerAccessCode",
        "BLOOM-",
        "patchJson(`/api/v1/admin/partners/${partnerId}`, { access_code: accessCode })",
    ):
        assert marker in source


def test_partner_access_forms_use_native_partner_selects() -> None:
    source = MAIN_JS.read_text(encoding="utf-8")

    assert "const renderNativePartnerSelect" in source
    assert '<select name="${escapeHtml(name)}"' in source
    assert source.count("Партнёр${renderNativePartnerSelect()}</label>") >= 2
    assert "Партнёры не загрузились" in source


def test_bot_staff_access_is_explained_separately() -> None:
    source = MAIN_JS.read_text(encoding="utf-8")

    assert "Доступ сотрудников партнёра в ботах" in source
    assert "Он не создаёт код для входа в ЛК партнёра" in source
