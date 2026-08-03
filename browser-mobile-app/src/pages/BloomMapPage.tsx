import { useEffect, useMemo, useRef, useState } from "react";
import type { Partner } from "../api/types";
import {
  buildYandexRouteUrl,
  buildTwoGisRouteUrl,
  distanceInKilometers,
  formatDistance,
  getPartnerCoordinates,
  type BloomCoordinates,
} from "../utils/bloomMap";
import { buildCatalogCategories, filterPartnersByCategory } from "../utils/catalogCategories";
import {
  getPartnerAddress,
  getPartnerCategories,
  getPartnerImage,
  getPartnerName,
  getPartnerPrivilege,
} from "../utils/partnerDisplay";

interface BloomMapPageProps {
  partners: Partner[];
  onBack: () => void;
  onOpenPartner: (partner: Partner) => void;
}

interface MapPartner {
  partner: Partner;
  point: BloomCoordinates;
}

type MapStatus = "loading" | "ready" | "missing-key" | "error";

const NOVOSIBIRSK_CENTER: [number, number] = [82.92043, 55.030204];
const MAP_SCRIPT_ID = "bloom-yandex-maps-api";
let runtimeKeyPromise: Promise<string> | null = null;

function getInjectedRuntimeKey(): string {
  const runtime = (window as Window & { __BLOOM_TG_CONFIG__?: { yandexMapsApiKey?: string } }).__BLOOM_TG_CONFIG__;
  return String(runtime?.yandexMapsApiKey || "").trim();
}

async function getRuntimeKey(): Promise<string> {
  const injected = getInjectedRuntimeKey();
  if (injected) return injected;
  runtimeKeyPromise ??= fetch("/api/runtime-config", { headers: { Accept: "application/json" }, cache: "no-store" })
    .then(async (response): Promise<{ yandexMapsApiKey?: string }> => response.ok ? response.json() : {})
    .then((payload) => String(payload.yandexMapsApiKey || "").trim())
    .catch(() => "");
  return runtimeKeyPromise;
}

async function loadYandexMaps(apiKey: string): Promise<Record<string, any>> {
  const existing = (window as Window & { ymaps3?: Record<string, any> }).ymaps3;
  if (existing) {
    await existing.ready;
    return existing;
  }

  const script = document.getElementById(MAP_SCRIPT_ID) as HTMLScriptElement | null
    ?? Object.assign(document.createElement("script"), {
      id: MAP_SCRIPT_ID,
      async: true,
      src: `https://api-maps.yandex.ru/v3/?apikey=${encodeURIComponent(apiKey)}&lang=ru_RU`,
    });
  if (!script.isConnected) document.head.appendChild(script);

  await new Promise<void>((resolve, reject) => {
    if ((window as Window & { ymaps3?: unknown }).ymaps3) return resolve();
    script.addEventListener("load", () => resolve(), { once: true });
    script.addEventListener("error", () => reject(new Error("yandex_maps_script_failed")), { once: true });
  });
  const loaded = (window as Window & { ymaps3?: Record<string, any> }).ymaps3;
  if (!loaded) throw new Error("yandex_maps_unavailable");
  await loaded.ready;
  return loaded;
}

function partnerKey(partner: Partner): string {
  return String(partner.id ?? partner.partner_id ?? getPartnerName(partner));
}

export function BloomMapPage({ partners, onBack, onOpenPartner }: BloomMapPageProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<any>(null);
  const [status, setStatus] = useState<MapStatus>("loading");
  const [selectedCategory, setSelectedCategory] = useState("Все");
  const [selectedPartnerId, setSelectedPartnerId] = useState<string | null>(null);
  const [userPoint, setUserPoint] = useState<BloomCoordinates | null>(null);
  const [locationMessage, setLocationMessage] = useState("");

  const mapPartners = useMemo<MapPartner[]>(() => partners.flatMap((partner) => {
    const point = getPartnerCoordinates(partner);
    return point ? [{ partner, point }] : [];
  }), [partners]);
  const categories = useMemo(() => buildCatalogCategories(mapPartners.map(({ partner }) => partner)), [mapPartners]);
  const visiblePartners = useMemo(() => {
    const filtered = filterPartnersByCategory(mapPartners.map(({ partner }) => partner), selectedCategory);
    const allowed = new Set(filtered.map(partnerKey));
    return mapPartners.filter(({ partner }) => allowed.has(partnerKey(partner)));
  }, [mapPartners, selectedCategory]);
  const selected = mapPartners.find(({ partner }) => partnerKey(partner) === selectedPartnerId) ?? null;

  useEffect(() => {
    let cancelled = false;
    let map: any = null;
    const container = mapContainerRef.current;
    if (!container) return;
    setStatus("loading");

    void (async () => {
      const apiKey = await getRuntimeKey();
      if (cancelled) return;
      if (!apiKey) {
        setStatus("missing-key");
        return;
      }
      try {
        const ymaps3 = await loadYandexMaps(apiKey);
        if (cancelled) return;
        const center = visiblePartners.length
          ? [visiblePartners[0].point.longitude, visiblePartners[0].point.latitude]
          : NOVOSIBIRSK_CENTER;
        map = new ymaps3.YMap(container, { location: { center, zoom: visiblePartners.length ? 12 : 11 } });
        map.addChild(new ymaps3.YMapDefaultSchemeLayer({ theme: "light" }));
        map.addChild(new ymaps3.YMapDefaultFeaturesLayer({ zIndex: 1800 }));
        visiblePartners.forEach(({ partner, point }) => {
          const marker = document.createElement("button");
          marker.type = "button";
          marker.className = "bloom-map-marker";
          marker.setAttribute("aria-label", `Открыть ${getPartnerName(partner)}`);
          marker.title = getPartnerName(partner);
          marker.innerHTML = '<span aria-hidden="true">✿</span>';
          marker.addEventListener("click", () => setSelectedPartnerId(partnerKey(partner)));
          map.addChild(new ymaps3.YMapMarker({ coordinates: [point.longitude, point.latitude], zIndex: 1900 }, marker));
        });
        mapInstanceRef.current = map;
        setStatus("ready");
      } catch {
        if (!cancelled) setStatus("error");
      }
    })();

    return () => {
      cancelled = true;
      map?.destroy?.();
      if (mapInstanceRef.current === map) mapInstanceRef.current = null;
      container.replaceChildren();
    };
  }, [visiblePartners]);

  const locateUser = () => {
    if (!navigator.geolocation) {
      setLocationMessage("Геолокация недоступна на этом устройстве.");
      return;
    }
    setLocationMessage("Определяем ваше местоположение…");
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const point = { latitude: coords.latitude, longitude: coords.longitude };
        setUserPoint(point);
        setLocationMessage("Расстояние до партнёров рассчитано.");
        mapInstanceRef.current?.update?.({ location: { center: [point.longitude, point.latitude], zoom: 13, duration: 300 } });
      },
      () => setLocationMessage("Не удалось получить геопозицию. Проверьте разрешение браузера."),
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 120000 },
    );
  };

  return (
    <section className="page bloom-map-page">
      <header className="bloom-map-header">
        <button className="bloom-map-back" type="button" onClick={onBack} aria-label="Вернуться к партнёрам">←</button>
        <div><p className="eyebrow">Рядом с вами</p><h1>Карта Bloom</h1></div>
        <button className="bloom-map-locate" type="button" onClick={locateUser}>⌖ <span>Я рядом</span></button>
      </header>

      <div className="chips bloom-map-chips" aria-label="Категории партнёров">
        {categories.map((category) => (
          <button className={category === selectedCategory ? "chip chip--active" : "chip"} type="button" key={category} onClick={() => { setSelectedCategory(category); setSelectedPartnerId(null); }}>
            {category}
          </button>
        ))}
      </div>
      {locationMessage ? <p className="bloom-map-location-message" role="status">{locationMessage}</p> : null}

      <div className="bloom-map-canvas-wrap">
        <div className="bloom-map-canvas" ref={mapContainerRef} aria-label="Карта партнёров Bloom Club" />
        {status === "loading" ? <div className="bloom-map-state" role="status"><span className="bloom-map-state__flower">✿</span><strong>Собираем места Bloom…</strong></div> : null}
        {status === "missing-key" ? <div className="bloom-map-state"><strong>Карта скоро появится</strong><p>Ключ карты ещё не подключён на сервере. Каталог партнёров продолжает работать.</p></div> : null}
        {status === "error" ? <div className="bloom-map-state"><strong>Не удалось открыть карту</strong><p>Проверьте соединение и попробуйте открыть экран ещё раз.</p></div> : null}
        {status === "ready" && !visiblePartners.length ? <div className="bloom-map-state bloom-map-state--compact"><strong>В этой категории пока нет меток</strong><p>Партнёры останутся доступны в каталоге.</p></div> : null}
      </div>

      <p className="bloom-map-summary">На карте: <strong>{visiblePartners.length}</strong> {visiblePartners.length === 1 ? "место" : "мест"}</p>

      {selected ? (
        <article className="bloom-map-card" aria-live="polite">
          {getPartnerImage(selected.partner) ? <img src={getPartnerImage(selected.partner)} alt="" /> : <div className="bloom-map-card__placeholder">✿</div>}
          <div className="bloom-map-card__content">
            <div className="bloom-map-card__meta">
              <span>{getPartnerCategories(selected.partner)[0] || "Партнёр Bloom"}</span>
              {userPoint ? <span>{formatDistance(distanceInKilometers(userPoint, selected.point))}</span> : null}
            </div>
            <h2>{getPartnerName(selected.partner)}</h2>
            <p>{getPartnerPrivilege(selected.partner)}</p>
            <small>{getPartnerAddress(selected.partner)}</small>
            <div className="bloom-map-card__actions">
              <button className="button button--primary" type="button" onClick={() => onOpenPartner(selected.partner)}>Открыть карточку</button>
              <a href={buildYandexRouteUrl(selected.point)} target="_blank" rel="noreferrer">Яндекс</a>
              <a href={buildTwoGisRouteUrl(selected.point)} target="_blank" rel="noreferrer">2ГИС</a>
            </div>
          </div>
        </article>
      ) : null}
    </section>
  );
}
