interface LoadingStateProps {
  title?: string;
  compact?: boolean;
}

export function LoadingState({ title = "Загружаем данные клуба", compact = false }: LoadingStateProps) {
  return (
    <div className={compact ? "state state--loading state--compact" : "state state--loading"} role="status">
      <video
        className="state__bloom-loader"
        autoPlay
        muted
        loop
        playsInline
        preload="metadata"
        aria-hidden="true"
      >
        <source src="/assets/loader/bloom-loader.mp4" type="video/mp4" />
      </video>
      <p>{title}</p>
    </div>
  );
}
