import { useEffect, useState } from "react";
import { checkInFlower, completeFlowerTask, getFlowerState } from "../api/client";
import type { FlowerState } from "../api/types";

const STAGE_NAMES = ["Семечко", "Росток", "Бутон", "Раскрывается", "Расцвёл"];

export function FlowerGame() {
  const [state, setState] = useState<FlowerState | null>(null);
  const [message, setMessage] = useState("");
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [showRating, setShowRating] = useState(false);

  useEffect(() => {
    let active = true;
    getFlowerState().then((result) => active && setState(result)).catch(() => active && setMessage("Цветок временно недоступен"));
    return () => { active = false; };
  }, []);

  async function run(action: "checkin" | number) {
    setBusyAction(String(action));
    setMessage("");
    try {
      const result = action === "checkin" ? await checkInFlower() : await completeFlowerTask(action);
      setState(result.state);
      setMessage(result.awarded ? (action === "checkin" ? "+1 лепесток. Цветок стал сильнее" : `+${result.state.tasks.find((task) => task.id === action)?.petals ?? 0} лепестка`) : "Сегодня уже выполнено");
    } catch {
      setMessage("Не удалось сохранить. Попробуйте ещё раз");
    } finally {
      setBusyAction(null);
    }
  }

  if (!state) {
    return <section className="flower-game flower-game--loading" aria-label="Цветок Bloom"><span className="flower-game__sprout" aria-hidden="true">🌱</span><p>{message || "Выращиваем ваш цветок…"}</p></section>;
  }

  const stage = Math.min(state.stage, STAGE_NAMES.length - 1);
  const progress = Math.min(100, Math.round((state.days_grown / Math.max(state.days_in_month, 1)) * 100));

  return (
    <section className="flower-game" aria-labelledby="flower-game-title">
      <div className="flower-game__heading">
        <div><p className="eyebrow">Цветок месяца</p><h2 id="flower-game-title">Сад Bloom</h2></div>
        <button className="flower-game__rank" type="button" onClick={() => setShowRating((value) => !value)} aria-expanded={showRating}>
          {state.rank ? `${state.rank} место` : "Рейтинг"}
        </button>
      </div>

      <div className={`flower-visual flower-visual--stage-${stage}`} aria-label={`Стадия: ${STAGE_NAMES[stage]}`}>
        <span className="flower-visual__glow" aria-hidden="true" />
        <span className="flower-visual__bloom" aria-hidden="true">{stage < 1 ? "•" : stage < 3 ? "🌱" : stage < 4 ? "🌷" : "🌸"}</span>
        <strong>{STAGE_NAMES[stage]}</strong>
        <small>{state.petals} лепестков · серия {state.streak} дн.</small>
      </div>

      <div className="flower-progress" aria-label={`Прогресс месяца ${progress}%`}>
        <span><i style={{ width: `${progress}%` }} /></span>
        <small>{state.days_grown} из {state.days_in_month} дней</small>
      </div>

      <button className="button button--primary flower-game__checkin" type="button" onClick={() => void run("checkin")} disabled={state.checked_in_today || busyAction !== null}>
        {state.checked_in_today ? "Лепесток сегодня получен" : busyAction === "checkin" ? "Добавляем лепесток…" : "Забрать лепесток"}
      </button>

      {state.tasks.length ? <div className="flower-tasks"><p className="eyebrow">Задание дня</p>{state.tasks.map((task) => <article key={task.id}>
        <div><strong>{task.title}</strong>{task.description ? <p>{task.description}</p> : null}<small>+{task.petals} лепестка</small></div>
        <button className="button button--secondary" type="button" onClick={() => void run(task.id)} disabled={task.completed_today || busyAction !== null}>{task.completed_today ? "Готово" : "Выполнить"}</button>
      </article>)}</div> : null}

      {message ? <p className="flower-game__message" role="status">{message}</p> : null}

      {showRating ? <div className="flower-leaderboard"><div className="flower-leaderboard__heading"><strong>Рейтинг месяца</strong><button type="button" onClick={() => setShowRating(false)} aria-label="Закрыть рейтинг">×</button></div>
        <p>Топ-10 получит дополнительные номерки после подведения итогов месяца.</p>
        {state.leaderboard.length ? <ol>{state.leaderboard.map((item) => <li className={item.is_current_user ? "is-current" : ""} key={item.client_id}><span>{item.place}</span><strong>{item.display_name}</strong><small>{item.petals} леп.</small></li>)}</ol> : <p>Рейтинг начнётся с первого лепестка.</p>}
      </div> : null}
    </section>
  );
}
