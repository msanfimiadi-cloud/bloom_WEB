import { memo } from "react";

interface LoadingStateProps {
  title?: string;
  compact?: boolean;
}

function LoadingStateComponent({ title = "Загружаем Bloom Club...", compact = false }: LoadingStateProps) {
  return (
    <div className={compact ? "state state--loading state--compact" : "state state--loading"} role="status" aria-live="polite">
      <video
        className="state__loader-video"
        src="/assets/loader/bloom-loader.mp4"
        autoPlay
        muted
        loop
        playsInline
        aria-hidden="true"
      />
      <p>{title}</p>
    </div>
  );
}

export const LoadingState = memo(LoadingStateComponent);
