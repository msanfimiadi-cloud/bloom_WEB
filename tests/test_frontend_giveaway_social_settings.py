from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_MAIN = ROOT / "frontend" / "src" / "main.js"


def test_social_settings_are_moved_to_extra_numbers_tab() -> None:
    source = FRONTEND_MAIN.read_text(encoding="utf-8")
    giveaway_payload_section = source.split("const buildGiveawayPayload = (form) => {", 1)[1].split(
        "const buildSocialGiveawaySettingsPayload",
        1,
    )[0]

    assert "id: 'extraNumbers'" in source
    assert "renderSocialGiveawaySettingsTab" in source
    assert "data-admin-social-giveaway-settings-form" in source
    assert "data-admin-social-giveaway-select" in source
    assert "buildSocialGiveawaySettingsPayload" in source
    assert "/social-settings" in source
    assert "telegram_community_url" not in giveaway_payload_section
    assert "vk_community_url" not in giveaway_payload_section
