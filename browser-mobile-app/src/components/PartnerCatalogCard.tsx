import type { Partner } from "../api/types";
import { AppImage } from "./AppImage";
import {
  getPartnerAddress,
  getPartnerCategories,
  getPartnerCity,
  getPartnerImage,
  getPartnerName,
  tracePartnerImageDiagnostic,
} from "../utils/partnerDisplay";

interface PartnerCatalogCardProps {
  partner: Partner;
  onOpen: (partner: Partner) => void;
  diagnosticContext: "home" | "catalog";
}

export function PartnerCatalogCard({ partner, onOpen, diagnosticContext }: PartnerCatalogCardProps) {
  const image = getPartnerImage(partner);
  const name = getPartnerName(partner);
  const categories = getPartnerCategories(partner).join(" • ") || "Партнёр Bloom Club";
  const place = [getPartnerCity(partner), getPartnerAddress(partner)].filter(Boolean).join(" · ");

  tracePartnerImageDiagnostic(`${diagnosticContext}_partner_image_mapped`, partner, image);

  return (
    <button
      className="home-partner-tile partner-catalog-card"
      type="button"
      onClick={() => onOpen(partner)}
      aria-label={`Открыть партнёра ${name}`}
    >
      <AppImage
        src={image}
        alt=""
        fit="cover"
        placeholder={name.slice(0, 1) || "Bloom"}
        placeholderClassName="home-partner-tile__placeholder image-placeholder image-placeholder--brand"
        onError={() => tracePartnerImageDiagnostic("image_load_error", partner, image)}
      />
      <span className="home-partner-tile__body">
        <strong>{name}</strong>
        <small>{categories}</small>
        {place ? <em>{place}</em> : null}
        <span className="home-partner-tile__cta">Смотреть</span>
      </span>
    </button>
  );
}
