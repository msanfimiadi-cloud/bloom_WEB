# MVP multi-city specification

Federal Women Club is federal and multi-city by design. The MVP keeps the
subscription global for the club while partner catalog visibility is prepared
for city filtering.

## City model

`City` is the canonical city dictionary for web/backend and partner catalog
filtering. The initial default cities are:

- Новосибирск (`novosibirsk`)
- Москва (`moscow`)
- Санкт-Петербург (`saint-petersburg`)
- Екатеринбург (`ekaterinburg`)
- Казань (`kazan`)

## Partner city ownership

One MVP partner belongs to one city through `Partner.city_id`. The previous
`city_code` field remains in the lightweight dataclass skeleton as a legacy
placeholder until persistence models are finalized.

No partner branches or locations are introduced in the MVP.

## Client selected city

`ClientProfile.selected_city_id` is nullable. It represents the city selected by
a client in VK bot and/or web once those flows are implemented. Subscription is
not city-specific in the MVP.

## Catalog/API plan

Catalog and partner list endpoints should accept optional filters:

- `city_id`
- `city_slug`

If neither filter is provided, the API may return the general active catalog.
When both are provided, future production code should validate that they refer to
the same city. The current backend is a lightweight dataclass skeleton, so this
PR adds a service-level filtering helper instead of fake HTTP endpoints.

## Women's club categories

The canonical category list is stored in `app/core/categories.py` and can be
mirrored by frontend/VK clients until a database-backed dictionary is needed.
