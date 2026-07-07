from __future__ import annotations

from app.core.categories import WOMEN_CLUB_CATEGORIES
from app.models.city import City
from app.models.client import ClientProfile
from app.models.partner import Partner
from app.services.partner_service import PartnerCatalogFilters, filter_partners_by_city


def test_city_model_creation() -> None:
    city = City(id=1, name="Новосибирск", slug="novosibirsk", sort_order=10)

    assert city.id == 1
    assert city.name == "Новосибирск"
    assert city.slug == "novosibirsk"
    assert city.is_active is None or city.is_active is True


def test_partner_and_client_have_nullable_city_links() -> None:
    partner = Partner(id=1, city_id=1, name="Beauty Partner")
    client = ClientProfile(id=1, user_id=10)

    assert partner.city_id == 1
    assert client.selected_city_id is None


def test_women_club_categories_contain_expected_values() -> None:
    assert "Красота" in WOMEN_CLUB_CATEGORIES
    assert "Маникюр / педикюр" in WOMEN_CLUB_CATEGORIES
    assert "Другое" in WOMEN_CLUB_CATEGORIES
    assert len(WOMEN_CLUB_CATEGORIES) == 15


def test_partner_city_filter_by_id_and_slug() -> None:
    partners = [
        Partner(id=1, city_id=1, name="NSK"),
        Partner(id=2, city_id=2, name="MSK"),
    ]

    assert filter_partners_by_city(partners, PartnerCatalogFilters(city_id=1)) == [partners[0]]
    assert filter_partners_by_city(
        partners,
        PartnerCatalogFilters(city_slug="moscow"),
        city_slug_to_id=lambda slug: {"moscow": 2}.get(slug),
    ) == [partners[1]]
