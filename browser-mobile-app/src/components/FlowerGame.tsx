import { useEffect, useState } from "react";
import { checkInFlower, getFlowerState, submitFlowerSpecialTask } from "../api/client";
import type { FlowerState } from "../api/types";

const STAGE_NAMES = ["Семечко", "Проклюнулось", "Росток", "Бутон", "Расцвёл"];

export function FlowerGame() {
  const [state, setState] = useState<FlowerState | null>(null);
  const [message, setMessage] = useState("");
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [showRating, setShowRating] = useState(false);
  const [showSpecialTask, setShowSpecialTask] = useState(false);
  const [specialAnswers, setSpecialAnswers] = useState<Record<number, number>>({});

  useEffect(() => {
    let active = true;
    getFlowerState().then((result) => active && setState(result)).catch(() => active && setMessage("Цветок временно недоступен"));
    return () => { active = false; };
  }, []);

  async function findPetal() {
    setBusyAction("checkin");
    setMessage("");
    try {
      const result = await checkInFlower();
      setState(result.state);
      setMessage(result.awarded ? `+${result.state.petal_reward} лепесток. Цветок стал сильнее` : "Сегодня лепесток уже найден");
    } catch {
      setMessage("Не удалось сохранить. Попробуйте ещё раз");
    } finally {
      setBusyAction(null);
    }
  }

  async function submitSpecial() {
    const task = state?.special_task;
    if (!task || task.questions.some((question) => !specialAnswers[question.id])) {
      setMessage("Ответьте на все вопросы");
      return;
    }
    setBusyAction("special");
    setMessage("");
    try {
      const result = await submitFlowerSpecialTask(task.id, task.questions.map((question) => ({ question_id: question.id, option_id: specialAnswers[question.id] })));
      setState(result.state);
      setShowSpecialTask(false);
      setMessage(result.awarded ? `Специальное задание выполнено · +${task.petals} лепестков` : "Задание уже выполнено");
    } catch {
      setMessage("Не удалось отправить ответы. Попробуйте ещё раз");
    } finally {
      setBusyAction(null);
    }
  }

  if (!state) {
    return <section className="flower-game flower-game--loading" aria-label="Цветок Bloom"><span className="flower-game__sprout" aria-hidden="true">🌱</span><p>{message || "Выращиваем ваш цветок…"}</p></section>;
  }

  const stage = Math.min(state.stage, STAGE_NAMES.length - 1);
  const progress = Math.min(100, Math.round((state.days_grown / Math.max(state.days_in_month, 1)) * 100));
  const specialTask = state.special_task;

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
        {!state.checked_in_today ? <button className={`flower-daily-petal flower-daily-petal--${state.petal_position}`} type="button" onClick={() => void findPetal()} disabled={busyAction !== null} aria-label={`Найти лепесток, +${state.petal_reward}`}><span aria-hidden="true">🌸</span></button> : null}
        <span className="flower-visual__bloom" aria-hidden="true">{stage < 1 ? "•" : stage < 3 ? "🌱" : stage < 4 ? "🌷" : "🌸"}</span>
        <strong>{STAGE_NAMES[stage]}</strong>
        <small>{state.petals} лепестков · серия {state.streak} дн.</small>
      </div>

      <div className="flower-progress" aria-label={`Прогресс месяца ${progress}%`}>
        <span><i style={{ width: `${progress}%` }} /></span>
        <small>{state.days_grown} из {state.days_in_month} дней</small>
      </div>

      <p className="flower-game__daily-hint">{state.checked_in_today ? "Лепесток сегодня найден" : "Задание дня: найдите лепесток в саду и нажмите на него"}</p>

      {specialTask ? <div className="flower-special-task"><p className="eyebrow">Задание недели</p><strong>{specialTask.title}</strong>{specialTask.description ? <p>{specialTask.description}</p> : null}<small>+{specialTask.petals} лепестков</small><button className="button button--secondary" type="button" onClick={() => setShowSpecialTask(true)} disabled={specialTask.completed || busyAction !== null}>{specialTask.completed ? "Задание выполнено" : "Специальное задание клуба"}</button></div> : null}

      {message ? <p className="flower-game__message" role="status">{message}</p> : null}

      {showSpecialTask && specialTask ? <div className="flower-special-modal" role="dialog" aria-modal="true" aria-label={specialTask.title}><div className="flower-special-modal__card"><button className="flower-special-modal__close" type="button" aria-label="Закрыть" onClick={() => setShowSpecialTask(false)}>×</button><p className="eyebrow">Специальное задание клуба</p><h3>{specialTask.title}</h3>{specialTask.questions.map((question, index) => <fieldset key={question.id}><legend>{index + 1}. {question.prompt}</legend>{question.options.map((option) => <label key={option.id}><input type="radio" name={`flower-question-${question.id}`} checked={specialAnswers[question.id] === option.id} onChange={() => setSpecialAnswers((answers) => ({ ...answers, [question.id]: option.id }))} /> <span>{option.label}</span></label>)}</fieldset>)}<button className="button button--primary" type="button" onClick={() => void submitSpecial()} disabled={busyAction !== null}>{busyAction === "special" ? "Отправляем…" : "Завершить задание"}</button></div></div> : null}

      {showRating ? <div className="flower-leaderboard"><div className="flower-leaderboard__heading"><strong>Рейтинг месяца</strong><button type="button" onClick={() => setShowRating(false)} aria-label="Закрыть рейтинг">×</button></div>
        <p>Участницы с одинаковым количеством лепестков делят одно место.</p>
        {state.leaderboard.length ? <ol>{state.leaderboard.map((item) => <li className={item.is_current_user ? "is-current" : ""} key={item.client_id}><span>{item.place}</span><strong>{item.display_name}</strong><small>{item.petals} леп.</small></li>)}</ol> : <p>Рейтинг начнётся с первого лепестка.</p>}
      </div> : null}
    </section>
  );
}
