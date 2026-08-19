from app.api.v1.endpoints.admin import _apply_giveaway_payload, _apply_social_giveaway_settings_payload
from app.models.giveaway import Giveaway
from app.schemas.giveaway import GiveawayPrizeWrite, GiveawayWrite, SocialGiveawaySettingsWrite


def test_regular_giveaway_update_keeps_existing_social_settings():
    from tests.test_giveaways import _session

    session = _session()
    giveaway = Giveaway(
        title="Август",
        is_active=True,
        winners_count=1,
        telegram_community_url="https://t.me/bloomclub",
        telegram_chat_id="-100123",
        telegram_reward_enabled=True,
        vk_community_url="https://vk.com/bloomclub",
        vk_group_id="321",
        vk_reward_enabled=True,
    )
    session.add(giveaway)
    session.flush()

    _apply_giveaway_payload(
        giveaway,
        GiveawayWrite(
            title="Август обновлён",
            description="Новые призы",
            is_active=False,
            winners_count=1,
            prizes=[GiveawayPrizeWrite(place_number=1, prize_title="Новый приз")],
        ),
    )

    assert giveaway.title == "Август обновлён"
    assert giveaway.telegram_community_url == "https://t.me/bloomclub"
    assert giveaway.telegram_chat_id == "-100123"
    assert giveaway.telegram_reward_enabled is True
    assert giveaway.vk_community_url == "https://vk.com/bloomclub"
    assert giveaway.vk_group_id == "321"
    assert giveaway.vk_reward_enabled is True


def test_social_settings_update_changes_only_social_fields():
    from tests.test_giveaways import _session

    session = _session()
    giveaway = Giveaway(
        title="Сентябрь",
        description="Основное описание",
        is_active=True,
        winners_count=2,
    )
    session.add(giveaway)
    session.flush()

    _apply_social_giveaway_settings_payload(
        giveaway,
        SocialGiveawaySettingsWrite(
            telegram_community_url="https://t.me/newchannel",
            telegram_chat_id="-100555",
            telegram_reward_enabled=True,
            vk_community_url="https://vk.com/newclub",
            vk_group_id="999",
            vk_reward_enabled=True,
        ),
    )

    assert giveaway.title == "Сентябрь"
    assert giveaway.description == "Основное описание"
    assert giveaway.is_active is True
    assert giveaway.winners_count == 2
    assert giveaway.telegram_community_url == "https://t.me/newchannel"
    assert giveaway.telegram_chat_id == "-100555"
    assert giveaway.telegram_reward_enabled is True
    assert giveaway.vk_community_url == "https://vk.com/newclub"
    assert giveaway.vk_group_id == "999"
    assert giveaway.vk_reward_enabled is True
