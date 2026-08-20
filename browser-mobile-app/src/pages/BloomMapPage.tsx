import { useEffect, useMemo, useRef, useState } from "react";
import type { Partner } from "../api/types";
import {
  buildYandexRouteUrl,
  buildTwoGisRouteUrl,
  BLOOM_MAP_RUNTIME_ERROR_EVENT,
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
type YandexMapsV2 = {
  ready: (callback: () => void) => void;
  Map: new (container: HTMLElement, state: Record<string, any>, options?: Record<string, any>) => any;
  Placemark: new (coordinates: [number, number], properties?: Record<string, any>, options?: Record<string, any>) => any;
  GeoObjectCollection: new (_?: Record<string, any>, options?: Record<string, any>) => {
    add: (item: any) => void;
    removeAll?: () => void;
    getBounds?: () => any;
  };
  templateLayoutFactory?: {
    createClass: (html: string) => any;
  };
};

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

async function loadYandexMaps(apiKey: string): Promise<YandexMapsV2> {
  const existing = (window as Window & { ymaps?: YandexMapsV2 }).ymaps;
  if (existing) {
    return existing;
  }

  const script = document.getElementById(MAP_SCRIPT_ID) as HTMLScriptElement | null
    ?? Object.assign(document.createElement("script"), {
      id: MAP_SCRIPT_ID,
      async: true,
      src: `https://api-maps.yandex.ru/2.1/?apikey=${encodeURIComponent(apiKey)}&lang=ru_RU`,
    });
  if (!script.isConnected) document.head.appendChild(script);

  await new Promise<void>((resolve, reject) => {
    if ((window as Window & { ymaps?: unknown }).ymaps) return resolve();
    script.addEventListener("load", () => resolve(), { once: true });
    script.addEventListener("error", () => reject(new Error("yandex_maps_script_failed")), { once: true });
  });
  const loaded = (window as Window & { ymaps?: YandexMapsV2 }).ymaps;
  if (!loaded) throw new Error("yandex_maps_unavailable");
  return loaded;
}

function partnerKey(partner: Partner): string {
  return String(partner.id ?? partner.partner_id ?? getPartnerName(partner));
}

export function BloomMapPage({ partners, onBack, onOpenPartner }: BloomMapPageProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<any>(null);
  const ymapsRef = useRef<YandexMapsV2 | null>(null);
  const markersCollectionRef = useRef<any>(null);
  const hasAppliedInitialViewportRef = useRef(false);
  const lastViewportCategoryRef = useRef<string | null>(null);
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
    let mapFailed = false;
    const container = mapContainerRef.current;
    if (!container) return;
    setStatus("loading");

    const handleMapRuntimeError = () => {
      if (cancelled || mapFailed) return;
      mapFailed = true;
      mapInstanceRef.current?.destroy?.();
      mapInstanceRef.current = null;
      markersCollectionRef.current = null;
      ymapsRef.current = null;
      container.replaceChildren();
      setStatus("error");
    };
    window.addEventListener(BLOOM_MAP_RUNTIME_ERROR_EVENT, handleMapRuntimeError);

    void (async () => {
      const apiKey = await getRuntimeKey();
      if (cancelled || mapFailed) return;
      if (!apiKey) {
        setStatus("missing-key");
        return;
      }
      try {
        const ymaps = await loadYandexMaps(apiKey);
        if (cancelled || mapFailed) return;
        ymapsRef.current = ymaps;
        ymaps.ready(() => {
          if (cancelled || mapFailed) return;
          const center = mapPartners.length
            ? [mapPartners[0].point.latitude, mapPartners[0].point.longitude]
            : [NOVOSIBIRSK_CENTER[1], NOVOSIBIRSK_CENTER[0]];
          const map = new ymaps.Map(
            container,
            {
              center,
              zoom: mapPartners.length ? 12 : 11,
              controls: ["zoomControl"],
            },
            {
              suppressMapOpenBlock: true,
              yandexMapDisablePoiInteractivity: true,
            },
          );
          const collection = new ymaps.GeoObjectCollection();
          map.geoObjects?.add?.(collection);
          markersCollectionRef.current = collection;
          mapInstanceRef.current = map;
          if (!mapFailed) setStatus("ready");
        });
      } catch {
        if (!cancelled) setStatus("error");
      }
    })();

    return () => {
      cancelled = true;
      window.removeEventListener(BLOOM_MAP_RUNTIME_ERROR_EVENT, handleMapRuntimeError);
      mapInstanceRef.current?.destroy?.();
      mapInstanceRef.current = null;
      markersCollectionRef.current = null;
      ymapsRef.current = null;
      container.replaceChildren();
    };
  }, []);

  useEffect(() => {
    if (status !== "ready") return;
    const ymaps = ymapsRef.current;
    const map = mapInstanceRef.current;
    if (!ymaps || !map) return;

    let collection = markersCollectionRef.current;
    if (!collection) {
      collection = new ymaps.GeoObjectCollection();
      map.geoObjects?.add?.(collection);
      markersCollectionRef.current = collection;
    }

    collection.removeAll?.();
    const nextViewportCategory = selectedCategory;

    visiblePartners.forEach(({ partner, point }) => {
      const placemark = new ymaps.Placemark(
        [point.latitude, point.longitude],
        {
          hintContent: getPartnerName(partner),
          balloonContent: getPartnerName(partner),
        },
        {
          preset: "islands#redIcon",
          iconColor: "#b84d72",
        },
      );
      placemark.events?.add?.("click", () => setSelectedPartnerId(partnerKey(partner)));
      collection.add(placemark);
    });

    const shouldRefreshViewport =
      !hasAppliedInitialViewportRef.current
      || lastViewportCategoryRef.current !== nextViewportCategory;

    if (shouldRefreshViewport) {
      if (visiblePartners.length > 1) {
        const bounds = collection.getBounds?.();
        if (bounds) {
          map.setBounds?.(bounds, {
            checkZoomRange: true,
            duration: 180,
            zoomMargin: 24,
          });
        }
      } else if (visiblePartners.length === 1) {
        map.setCenter?.(
          [visiblePartners[0].point.latitude, visiblePartners[0].point.longitude],
          13,
          { duration: 180 },
        );
      } else {
        map.setCenter?.([NOVOSIBIRSK_CENTER[1], NOVOSIBIRSK_CENTER[0]], 11, { duration: 180 });
      }

      hasAppliedInitialViewportRef.current = true;
      lastViewportCategoryRef.current = nextViewportCategory;
    }
  }, [selectedCategory, status, visiblePartners]);

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
        mapInstanceRef.current?.setCenter?.([point.latitude, point.longitude], 13, { duration: 300 });
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
