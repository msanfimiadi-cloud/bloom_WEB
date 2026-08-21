from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.partner import Partner, PartnerLocation, PartnerOffer
from app.models.verification import PrivilegeVerificationSession


def normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def sorted_partner_locations(partner: Partner) -> list[PartnerLocation]:
    return sorted(
        list(getattr(partner, "locations", []) or []),
        key=lambda item: (item.sort_order, item.id or 0),
    )


def primary_partner_location(partner: Partner) -> PartnerLocation | None:
    locations = sorted_partner_locations(partner)
    if locations:
        return locations[0]
    return None


def fallback_partner_location_payload(partner: Partner) -> dict[str, Any] | None:
    address = normalize_optional_text(partner.address)
    phone = normalize_optional_text(partner.phone)
    map_url = normalize_optional_text(partner.map_url)
    working_hours = normalize_optional_text(partner.working_hours)
    has_coordinates = partner.latitude is not None and partner.longitude is not None
    if not any([address, phone, map_url, working_hours, has_coordinates]):
        return None
    return {
        "id": None,
        "partner_id": partner.id,
        "name": None,
        "address": address,
        "phone": phone,
        "map_url": map_url,
        "latitude": float(partner.latitude) if partner.latitude is not None else None,
        "longitude": float(partner.longitude) if partner.longitude is not None else None,
        "working_hours": working_hours,
        "is_active": True,
        "sort_order": 0,
    }


def resolved_partner_locations_payload(partner: Partner) -> list[dict[str, Any]]:
    locations = sorted_partner_locations(partner)
    if locations:
        return [
            {
                "id": location.id,
                "partner_id": location.partner_id,
                "name": location.name,
                "address": location.address,
                "phone": location.phone,
                "map_url": location.map_url,
                "latitude": float(location.latitude) if location.latitude is not None else None,
                "longitude": float(location.longitude) if location.longitude is not None else None,
                "working_hours": location.working_hours,
                "is_active": bool(location.is_active),
                "sort_order": int(location.sort_order or 0),
            }
            for location in locations
        ]
    fallback = fallback_partner_location_payload(partner)
    return [fallback] if fallback is not None else []


def location_or_partner_field(location: PartnerLocation | None, partner: Partner, field: str) -> Any:
    if location is not None:
        return getattr(location, field)
    return getattr(partner, field)


def mirror_primary_location_to_partner(partner: Partner) -> None:
    primary = primary_partner_location(partner)
    if primary is None:
        return
    partner.address = primary.address
    partner.phone = primary.phone
    partner.map_url = primary.map_url
    partner.latitude = primary.latitude
    partner.longitude = primary.longitude
    partner.working_hours = primary.working_hours


def ensure_partner_location(db: Session, partner_id: int, location_id: int | None) -> PartnerLocation | None:
    if location_id is None:
        return None
    location = db.execute(
        select(PartnerLocation).where(
            PartnerLocation.id == location_id,
            PartnerLocation.partner_id == partner_id,
        )
    ).scalar_one_or_none()
    if location is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner location not found")
    return location


def sync_partner_locations(db: Session, partner: Partner, payload_locations: list[dict[str, Any]] | None) -> None:
    if payload_locations is None:
        return

    existing_by_id = {location.id: location for location in sorted_partner_locations(partner) if location.id is not None}
    kept_ids: set[int] = set()

    for index, raw_item in enumerate(payload_locations):
        location_id = raw_item.get("id")
        address = normalize_optional_text(raw_item.get("address"))
        name = normalize_optional_text(raw_item.get("name"))
        phone = normalize_optional_text(raw_item.get("phone"))
        map_url = normalize_optional_text(raw_item.get("map_url"))
        working_hours = normalize_optional_text(raw_item.get("working_hours"))
        is_active = bool(raw_item.get("is_active", True))
        sort_order = raw_item.get("sort_order")
        latitude = raw_item.get("latitude")
        longitude = raw_item.get("longitude")

        if location_id is None and not any([address, name, phone, map_url, working_hours, latitude, longitude]):
            continue

        if address is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="partner_location_address_required")

        if location_id is None:
            location = PartnerLocation(partner_id=partner.id)
            db.add(location)
        else:
            location = existing_by_id.get(int(location_id))
            if location is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner location not found")
            kept_ids.add(location.id)

        location.name = name
        location.address = address
        location.phone = phone
        location.map_url = map_url
        location.latitude = Decimal(str(latitude)) if latitude is not None else None
        location.longitude = Decimal(str(longitude)) if longitude is not None else None
        location.working_hours = working_hours
        location.is_active = is_active
        location.sort_order = int(sort_order if sort_order is not None else index)

    removable = [
        location
        for location_id, location in existing_by_id.items()
        if location_id not in kept_ids and all(raw.get("id") != location_id for raw in payload_locations)
    ]
    for location in removable:
        db.query(PartnerOffer).filter(PartnerOffer.location_id == location.id).update({"location_id": None})
        db.query(PrivilegeVerificationSession).filter(PrivilegeVerificationSession.location_id == location.id).update({"location_id": None})
        db.delete(location)

    db.flush()
    mirror_primary_location_to_partner(partner)
