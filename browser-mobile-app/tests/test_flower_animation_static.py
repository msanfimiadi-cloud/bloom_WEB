from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FLOWER = (ROOT / "src/components/FlowerGame.tsx").read_text(encoding="utf-8")
STYLES = (ROOT / "src/styles.css").read_text(encoding="utf-8")


def test_flower_stages_use_branded_media() -> None:
    assert "/assets/garden/stage-${stage}.jpeg" in FLOWER
    assert "/assets/garden/bloom-flower-loop.mp4" in FLOWER
    assert 'poster="/assets/garden/stage-4.jpeg"' in FLOWER
    for attribute in ["autoPlay", "muted", "loop", "playsInline"]:
        assert attribute in FLOWER


def test_flower_motion_is_accessible_and_transform_only() -> None:
    assert 'matchMedia("(prefers-reduced-motion: reduce)")' in FLOWER
    assert "@keyframes bloom-garden-seed-alive" in STYLES
    assert "@keyframes bloom-garden-germinated-alive" in STYLES
    assert "@keyframes bloom-garden-sprout-alive" in STYLES
    assert "@keyframes bloom-garden-bud-alive" in STYLES
    reduced_motion = STYLES[STYLES.index("@media (prefers-reduced-motion: reduce)") :]
    assert ".flower-stage-media" in reduced_motion
    assert "animation: none" in reduced_motion
