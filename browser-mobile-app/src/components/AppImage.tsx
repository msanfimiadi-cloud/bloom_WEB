import type { CSSProperties } from "react";
import { useLayoutEffect, useRef, useState } from "react";

interface AppImageProps {
  src?: string | null;
  alt?: string;
  className?: string;
  shellClassName?: string;
  placeholderClassName?: string;
  placeholder?: string;
  loading?: "eager" | "lazy";
  fit?: "cover" | "contain" | "smart";
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
  const shellRef = useRef<HTMLSpanElement | null>(null);
  const [loadedSrc, setLoadedSrc] = useState("");
  const [failedSrc, setFailedSrc] = useState("");
  const [resolvedFit, setResolvedFit] = useState<"cover" | "contain">(fit === "contain" ? "contain" : "cover");
  const safeSrc = typeof src === "string" && src.trim() ? src : "";
  const isLoaded = Boolean(safeSrc) && loadedSrc === safeSrc;
  const hasError = Boolean(safeSrc) && failedSrc === safeSrc;

  function updateResolvedFit() {
    if (fit !== "smart") {
      setResolvedFit(fit === "contain" ? "contain" : "cover");
      return;
    }

    const image = imageRef.current;
    const shell = shellRef.current;
    if (!image || !shell || image.naturalWidth <= 0 || image.naturalHeight <= 0) {
      setResolvedFit("cover");
      return;
    }

    const shellWidth = shell.clientWidth;
    const shellHeight = shell.clientHeight;
    if (shellWidth <= 0 || shellHeight <= 0) {
      setResolvedFit("cover");
      return;
    }

    const imageRatio = image.naturalWidth / image.naturalHeight;
    const shellRatio = shellWidth / shellHeight;
    const cropRisk = Math.max(imageRatio / shellRatio, shellRatio / imageRatio);
    setResolvedFit(cropRisk >= 1.38 ? "contain" : "cover");
  }

  useLayoutEffect(() => {
    const image = imageRef.current;
    if (image?.complete && image.naturalWidth > 0) {
      setLoadedSrc(safeSrc);
      updateResolvedFit();
    }
  }, [safeSrc]);

  useLayoutEffect(() => {
    if (fit !== "smart" || typeof window === "undefined") {
      return;
    }

    updateResolvedFit();

    const shell = shellRef.current;
    if (!shell || typeof ResizeObserver === "undefined") {
      return;
    }

    const observer = new ResizeObserver(() => updateResolvedFit());
    observer.observe(shell);
    return () => observer.disconnect();
  }, [fit, safeSrc, isLoaded]);

  if (!safeSrc || hasError) {
    return (
      <span className={placeholderClassName} aria-label="Изображение скоро появится">
        <span>{placeholder}</span>
      </span>
    );
  }

  return (
    <span
      ref={shellRef}
      className={["image-shell", isLoaded ? "image-shell--loaded" : "", `image-shell--${resolvedFit}`, shellClassName].filter(Boolean).join(" ")}
      style={{ "--image-shell-bg": `url("${safeSrc}")` } as CSSProperties}
    >
      <span className="image-shell__skeleton" aria-hidden="true" />
      <span className="image-shell__overlay" aria-hidden="true" />
      <img
        ref={imageRef}
        className={className}
        src={safeSrc}
        alt={alt}
        loading={loading}
        decoding="async"
        onLoad={() => {
          setLoadedSrc(safeSrc);
          updateResolvedFit();
        }}
        onError={() => {
          setFailedSrc(safeSrc);
          onError?.();
        }}
      />
    </span>
  );
}
