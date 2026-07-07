from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from app.models.partner import Partner


@dataclass(frozen=True, slots=True)
class PartnerCatalogFilters:
    city_id: int | None = None
    city_slug: str | None = None


def filter_partners_by_city(
    partners: Iterable[Partner],
    filters: PartnerCatalogFilters,
    *,
    city_slug_to_id: Callable[[str], int | None] | None = None,
) -> list[Partner]:
    """Apply the MVP city filter to an in-memory partner collection.

    Real persistence-backed catalog endpoints can reuse this contract while the
    imported backend remains a light dataclass skeleton.
    """
    selected_city_id = filters.city_id
    if selected_city_id is None and filters.city_slug and city_slug_to_id:
        selected_city_id = city_slug_to_id(filters.city_slug)

    if selected_city_id is None:
        return list(partners)

    return [partner for partner in partners if partner.city_id == selected_city_id]
