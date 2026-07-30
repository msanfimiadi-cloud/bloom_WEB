import { useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";
import { checkInFlower, getFlowerState, submitFlowerSpecialTask } from "../api/client";
import type { FlowerState } from "../api/types";

const STAGE_NAMES = ["Семечко", "Проклюнулось", "Росток", "Бутон", "Расцвёл"];
const STAGE_STARTS = [0, 5, 12, 22, 35];
const STAGE_ENDS = [4, 11, 21, 34, 35];

function getStageProgress(petals: number, stage: number) {
  if (stage >= STAGE_NAMES.length - 1) return 1;
  const start = STAGE_STARTS[stage];
  const end = STAGE_ENDS[stage];
  return Math.max(0, Math.min(1, (petals - start) / Math.max(end - start, 1)));
}

function getMonthProgress(daysInMonth: number, currentDay: number) {
  const safeDaysInMonth = Math.max(daysInMonth, 1);
  const elapsedDays = Math.min(safeDaysInMonth, Math.max(currentDay, 1));
  const remainingDays = Math.max(0, safeDaysInMonth - elapsedDays);
  const progress = Math.min(100, Math.round((elapsedDays / safeDaysInMonth) * 100));
  return { progress, remainingDays };
}

function formatRemainingDays(remainingDays: number) {
  if (remainingDays === 0) return "Сегодня последний день месяца";
  const mod100 = remainingDays % 100;
  const mod10 = remainingDays % 10;
  const word = mod100 >= 11 && mod100 <= 14 ? "дней" : mod10 === 1 ? "день" : mod10 >= 2 && mod10 <= 4 ? "дня" : "дней";
  return `До конца месяца осталось ${remainingDays} ${word}`;
}

function FlowerIllustration({ stage, stageProgress }: { stage: number; stageProgress: number }) {
  const progressStyle = { "--stage-progress": stageProgress } as CSSProperties;
  const prefersReducedMotion = typeof window !== "undefined"
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (stage === 4 && !prefersReducedMotion) {
    return (
      <video
        className="flower-stage-media flower-stage-media--video"
        style={progressStyle}
        autoPlay
        muted
        loop
        playsInline
        preload="metadata"
        poster="/assets/garden/stage-4.jpeg"
        aria-label={STAGE_NAMES[stage]}
      >
        <source src="/assets/garden/bloom-flower-loop.mp4" type="video/mp4" />
      </video>
    );
  }

  return (
    <img
      className={`flower-stage-media flower-stage-media--image flower-stage-media--stage-${stage}`}
      style={progressStyle}
      src={`/assets/garden/stage-${stage}.jpeg`}
      alt={STAGE_NAMES[stage]}
      decoding="async"
      loading="eager"
    />
  );
}

export function FlowerGame() {
  const [state, setState] = useState<FlowerState | null>(null);
  const [message, setMessage] = useState("");
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [showRating, setShowRating] = useState(false);
  const [showSpecialTask, setShowSpecialTask] = useState(false);
  const [specialAnswers, setSpecialAnswers] = useState<Record<number, number>>({});
  const [isPetalJoining, setIsPetalJoining] = useState(false);
  const [isStageChanging, setIsStageChanging] = useState(false);
  const petalAnimationTimeoutRef = useRef<number | null>(null);
  const stageAnimationTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    let active = true;
    getFlowerState().then((result) => active && setState(result)).catch(() => active && setMessage("Цветок временно недоступен"));
    return () => {
      active = false;
      if (petalAnimationTimeoutRef.current !== null) window.clearTimeout(petalAnimationTimeoutRef.current);
      if (stageAnimationTimeoutRef.current !== null) window.clearTimeout(stageAnimationTimeoutRef.current);
    };
  }, []);

  function updateFlowerState(nextState: FlowerState) {
    if (state && nextState.stage !== state.stage) {
      setIsStageChanging(true);
      if (stageAnimationTimeoutRef.current !== null) window.clearTimeout(stageAnimationTimeoutRef.current);
      stageAnimationTimeoutRef.current = window.setTimeout(() => {
        setIsStageChanging(false);
        stageAnimationTimeoutRef.current = null;
      }, 1050);
    }
    setState(nextState);
  }

  async function findPetal() {
    setBusyAction("checkin");
    setMessage("");
    try {
      const result = await checkInFlower();
      updateFlowerState(result.state);
      if (result.awarded) {
        setIsPetalJoining(true);
        petalAnimationTimeoutRef.current = window.setTimeout(() => {
          setIsPetalJoining(false);
          petalAnimationTimeoutRef.current = null;
        }, 850);
      }
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
      updateFlowerState(result.state);
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
  const stageProgress = getStageProgress(state.petals, stage);
  const { progress, remainingDays } = getMonthProgress(state.days_in_month, new Date().getDate());
  const specialTask = state.special_task;
  const nextStage = stage < STAGE_NAMES.length - 1 ? stage + 1 : null;
  const petalsToNextStage = nextStage === null ? 0 : Math.max(0, STAGE_STARTS[nextStage] - state.petals);

  return (
    <section className="flower-game" aria-labelledby="flower-game-title">
      <div className="flower-game__heading">
        <div><p className="eyebrow">Цветок месяца</p><h2 id="flower-game-title">Сад Bloom</h2></div>
        <button className="flower-game__rank" type="button" onClick={() => setShowRating((value) => !value)} aria-expanded={showRating}>
          {state.rank ? `${state.rank} место` : "Рейтинг"}
        </button>
      </div>

      <div className={`flower-visual flower-visual--stage-${stage}${isStageChanging ? " is-stage-changing" : ""}`} style={{ "--stage-progress": stageProgress } as CSSProperties} aria-label={`Стадия: ${STAGE_NAMES[stage]}`}>
        <span className="flower-visual__glow" aria-hidden="true" />
        {isPetalJoining ? <span className="flower-joining-petal" aria-hidden="true" /> : null}
        <div className="flower-visual__bloom"><FlowerIllustration stage={stage} stageProgress={stageProgress} /></div>
        <strong>{STAGE_NAMES[stage]}</strong>
        <small>{state.petals} лепестков · серия {state.streak} дн.</small>
      </div>

      <div className="flower-stage-path" aria-label={`Этап ${stage + 1} из ${STAGE_NAMES.length}`}>
        <div className="flower-stage-path__line" aria-hidden="true"><i style={{ width: `${((stage + (nextStage === null ? 0 : stageProgress)) / (STAGE_NAMES.length - 1)) * 100}%` }} /></div>
        <ol>
          {STAGE_NAMES.map((name, index) => (
            <li className={index < stage ? "is-complete" : index === stage ? "is-current" : ""} key={name}>
              <span aria-hidden="true">{index < stage ? "✓" : index + 1}</span>
              <small>{name}</small>
            </li>
          ))}
        </ol>
        <p>{nextStage === null ? "Цветок полностью расцвёл" : `До стадии «${STAGE_NAMES[nextStage]}» — ${petalsToNextStage} лепестков`}</p>
      </div>

      {!state.checked_in_today ? (
        <button className="button button--secondary flower-game__checkin" type="button" onClick={() => void findPetal()} disabled={busyAction !== null}>
          {busyAction === "checkin" ? "Добавляем лепесток…" : `Добавить лепесток дня · +${state.petal_reward}`}
        </button>
      ) : null}

      <div className="flower-progress" aria-label={`Прогресс месяца ${progress}%`}>
        <span><i style={{ width: `${progress}%` }} /></span>
        <small>{formatRemainingDays(remainingDays)}</small>
      </div>

      <p className="flower-game__daily-hint">{state.checked_in_today ? "Лепесток сегодня присоединился к цветку" : "Задание дня: добавьте новый лепесток к цветку"}</p>

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
