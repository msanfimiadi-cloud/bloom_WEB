import { readFileSync } from "node:fs";

const format = readFileSync(new URL("../src/utils/format.ts", import.meta.url), "utf8");
const partnerPage = readFileSync(new URL("../src/pages/PartnerPage.tsx", import.meta.url), "utf8");

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

assert(
  format.includes("export function normalizePartnerMapUrl"),
  "partner map links must be normalized before they are opened",
);
assert(
  /2gis\\\\\.\\(ru\\|com\\|kz\\|kg\\|uz\\|ae\\|cl\\)/.test(format),
  "2GIS domains must be accepted explicitly",
);
assert(
  format.includes('parsedUrl.protocol === "https:"') && format.includes('parsedUrl.protocol === "http:"'),
  "only HTTP(S) partner map links may be opened",
);
assert(
  format.includes("normalizePartnerMapUrl(options.mapUrl) ?? buildYandexMapsUrl(options)"),
  "invalid or missing saved links must fall back to the existing Yandex Maps URL",
);
assert(
  partnerPage.includes("buildPartnerMapsUrl") && partnerPage.includes("mapUrl: currentPartner.map_url"),
  "PartnerPage must prefer the map link saved for the partner",
);
assert(
  partnerPage.includes('href={mapsUrl}') && partnerPage.includes('target="_blank"'),
  "the map action must open the resolved provider link in a new tab",
);

console.log("Partner map link regression checks passed.");
