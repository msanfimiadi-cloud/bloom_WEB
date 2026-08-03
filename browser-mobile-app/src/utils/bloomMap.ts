import type { Partner } from "../api/types";
import { toText } from "./text";

export interface BloomCoordinates {
  latitude: number;
  longitude: number;
}

export const BLOOM_MAP_RUNTIME_ERROR_EVENT = "bloom:map-runtime-error";

export function isRecoverableYandexMapsError(reason: unknown): boolean {
  const message = reason instanceof Error
    ? reason.message
    : typeof reason === "object" && reason && "message" in reason
      ? String((reason as { message?: unknown }).message ?? "")
      : String(reason ?? "");

  return /api-maps\.yandex\.ru|coverage fetch failed|yandex_maps_/i.test(message);
}

function isValidCoordinates(latitude: number, longitude: number): boolean {
  return Number.isFinite(latitude)
    && Number.isFinite(longitude)
    && latitude >= -90
    && latitude <= 90
    && longitude >= -180
    && longitude <= 180;
}

function coordinates(latitude: unknown, longitude: unknown): BloomCoordinates | null {
  const parsedLatitude = Number(latitude);
  const parsedLongitude = Number(longitude);
  return isValidCoordinates(parsedLatitude, parsedLongitude)
    ? { latitude: parsedLatitude, longitude: parsedLongitude }
    : null;
}

function parsePair(value: string, order: "lon-lat" | "lat-lon"): BloomCoordinates | null {
  const parts = value.split(/[~,;|]/).map((part) => Number(part.trim())).filter(Number.isFinite);
  if (parts.length < 2) return null;
  return order === "lon-lat" ? coordinates(parts[1], parts[0]) : coordinates(parts[0], parts[1]);
}

function coordinatesFromMapUrl(value: unknown): BloomCoordinates | null {
  const rawUrl = toText(value);
  if (!rawUrl) return null;

  try {
    const parsed = new URL(/^[a-z][a-z\d+.-]*:\/\//i.test(rawUrl) ? rawUrl : `https://${rawUrl}`);
    for (const key of ["ll", "pt"]) {
      const pair = parsed.searchParams.get(key);
      const result = pair ? parsePair(pair, "lon-lat") : null;
      if (result) return result;
    }

    const routeText = parsed.searchParams.get("rtext");
    if (routeText) {
      const routeParts = routeText.split("~").filter(Boolean);
      const destination = routeParts[routeParts.length - 1];
      const result = destination ? parsePair(destination, "lat-lon") : null;
      if (result) return result;
    }

    const pathPair = parsed.pathname.match(/(?:geo|firm|directions\/points)[^?#]*?(-?\d{1,3}(?:\.\d+)?)[,/](-?\d{1,2}(?:\.\d+)?)(?:\/|$)/i);
    if (pathPair) return coordinates(pathPair[2], pathPair[1]);
  } catch {
    return null;
  }

  return null;
}

export function getPartnerCoordinates(partner: Partner): BloomCoordinates | null {
  return coordinates(partner.latitude ?? partner.lat, partner.longitude ?? partner.lon)
    ?? coordinatesFromMapUrl(partner.map_url)
    ?? (() => {
      const raw = toText(partner.coordinates);
      return raw ? parsePair(raw, "lat-lon") : null;
    })();
}

export function buildYandexRouteUrl(point: BloomCoordinates): string {
  return `https://yandex.ru/maps/?rtext=~${point.latitude},${point.longitude}&rtt=auto`;
}

export function buildTwoGisRouteUrl(point: BloomCoordinates): string {
  return `https://2gis.ru/directions/points/|${point.longitude},${point.latitude}`;
}

export function distanceInKilometers(from: BloomCoordinates, to: BloomCoordinates): number {
  const radians = (degrees: number) => degrees * Math.PI / 180;
  const earthRadius = 6371;
  const latitudeDelta = radians(to.latitude - from.latitude);
  const longitudeDelta = radians(to.longitude - from.longitude);
  const a = Math.sin(latitudeDelta / 2) ** 2
    + Math.cos(radians(from.latitude)) * Math.cos(radians(to.latitude)) * Math.sin(longitudeDelta / 2) ** 2;
  return earthRadius * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export function formatDistance(kilometers: number): string {
  if (kilometers < 1) return `${Math.max(10, Math.round(kilometers * 1000 / 10) * 10)} м`;
  return `${kilometers.toFixed(kilometers < 10 ? 1 : 0).replace(".", ",")} км`;
}
