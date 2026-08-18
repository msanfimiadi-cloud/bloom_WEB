import { useLayoutEffect, useRef, useState } from "react";

interface AppImageProps {
  src?: string | null;
  alt?: string;
  className?: string;
  shellClassName?: string;
  placeholderClassName?: string;
  placeholder?: string;
  loading?: "eager" | "lazy";
  fit?: "cover" | "contain";
  onError?: () => void;
}

export function AppImage({
  src,
  alt = "",
  className,
  shellClassName = "",
  placeholderClassName = "image-placeholder",
  placeholder = "Bloom",
  loading = "lazy",
  fit = "cover",
  onError,
}: AppImageProps) {
  const imageRef = useRef<HTMLImageElement | null>(null);
  const [loadedSrc, setLoadedSrc] = useState("");
  const [failedSrc, setFailedSrc] = useState("");
  const safeSrc = typeof src === "string" && src.trim() ? src : "";
  const isLoaded = Boolean(safeSrc) && loadedSrc === safeSrc;
  const hasError = Boolean(safeSrc) && failedSrc === safeSrc;

  useLayoutEffect(() => {
    const image = imageRef.current;
    if (image?.complete && image.naturalWidth > 0) {
      setLoadedSrc(safeSrc);
    }
  }, [safeSrc]);

  if (!safeSrc || hasError) {
    return (
      <span className={placeholderClassName} aria-label="Изображение скоро появится">
        <span>{placeholder}</span>
      </span>
    );
  }

  return (
    <span className={["image-shell", isLoaded ? "image-shell--loaded" : "", `image-shell--${fit}`, shellClassName].filter(Boolean).join(" ")}>
      <span className="image-shell__skeleton" aria-hidden="true" />
      <span className="image-shell__overlay" aria-hidden="true" />
      <img
        ref={imageRef}
        className={className}
        src={safeSrc}
        alt={alt}
        loading={loading}
        decoding="async"
        onLoad={() => setLoadedSrc(safeSrc)}
        onError={() => {
          setFailedSrc(safeSrc);
          onError?.();
        }}
      />
    </span>
  );
}
