from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_admin_defaults_and_validates_monthly_draw_on_sixteenth() -> None:
    frontend = (ROOT / "frontend" / "src" / "main.js").read_text(encoding="utf-8")

    assert "const nextGiveawayDrawInput" in frontend
    assert "-16T12:00" in frontend
    assert "Дата розыгрыша — 16-е число" in frontend
    assert "Розыгрыши проводятся 16-го числа каждого месяца по новосибирскому времени." in frontend
    assert "novosibirskDateTimeToIso(fd.get('ends_at'))" in frontend
    assert "ежемесячным розыгрышам 16-го числа" in frontend


def test_public_giveaway_contract_exposes_draw_date() -> None:
    schema = (ROOT / "app" / "schemas" / "giveaway.py").read_text(encoding="utf-8")
    endpoint = (ROOT / "app" / "api" / "v1" / "endpoints" / "clients.py").read_text(encoding="utf-8")

    assert "draws_at: datetime | None = None" in schema
    assert "draws_at=giveaway.ends_at" in endpoint
