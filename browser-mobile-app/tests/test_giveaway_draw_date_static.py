from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "src"


def test_client_shows_the_sixteenth_as_giveaway_date() -> None:
    home = (ROOT / "pages" / "HomePage.tsx").read_text(encoding="utf-8")
    app = (ROOT / "App.tsx").read_text(encoding="utf-8")
    types = (ROOT / "api" / "types.ts").read_text(encoding="utf-8")

    assert "giveaway.draws_at" in home
    assert "Розыгрыши Bloom Club проводятся 16-го числа каждого месяца." in home
    assert "draws_at?: BackendText" in types
    assert "<LoginGiveawayPreview" in app
    assert "Следующий розыгрыш — {formatGiveawayDay(giveaway?.draws_at)}" in app
    assert "Оформите подписку и получите номер участницы." in app
    assert "getGiveawayState()" in app
    assert "loginGiveawayRequestedRef.current" in app
