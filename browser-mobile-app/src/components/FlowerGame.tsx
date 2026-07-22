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

function FlowerIllustration({ stage, stageProgress }: { stage: number; stageProgress: number }) {
  const progressStyle = { "--stage-progress": stageProgress } as CSSProperties;
  return (
    <svg className={`flower-illustration flower-illustration--stage-${stage}`} style={progressStyle} viewBox="0 0 220 190" role="img" aria-label={STAGE_NAMES[stage]}>
      <defs>
        <linearGradient id="bloom-soil" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#8b5f56" />
          <stop offset="1" stopColor="#5f3d3b" />
        </linearGradient>
        <linearGradient id="bloom-stem" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#47795c" />
          <stop offset=".55" stopColor="#6fa276" />
          <stop offset="1" stopColor="#3e6d52" />
        </linearGradient>
        <radialGradient id="bloom-petal" cx="50%" cy="35%" r="70%">
          <stop offset="0" stopColor="#fff5f8" />
          <stop offset=".62" stopColor="#e9a6bd" />
          <stop offset="1" stopColor="#bd6688" />
        </radialGradient>
        <filter id="bloom-shadow" x="-30%" y="-30%" width="160%" height="180%">
          <feDropShadow dx="0" dy="6" stdDeviation="6" floodColor="#5b364e" floodOpacity=".18" />
        </filter>
      </defs>

      <ellipse className="flower-illustration__ground-shadow" cx="110" cy="161" rx="67" ry="13" />
      <path className="flower-illustration__soil" d="M43 157c6-28 27-42 67-42s61 14 67 42c-16 13-118 13-134 0Z" fill="url(#bloom-soil)" filter="url(#bloom-shadow)" />
      <path className="flower-illustration__soil-light" d="M55 145c22-13 87-13 109 0-22 8-87 8-109 0Z" />

      {stage === 0 ? (
        <g className="flower-illustration__seed flower-illustration__seed--resting" filter="url(#bloom-shadow)">
          <path d="M88 120c0-18 12-31 27-31 14 0 24 11 24 25 0 19-16 31-34 29-11-2-17-10-17-23Z" />
          <path className="flower-illustration__seed-shine" d="M101 102c6-6 14-7 20-3" />
          <path className="flower-illustration__seed-crack" d="m116 89-5 10 7 7-8 11" />
        </g>
      ) : null}

      {stage >= 1 ? (
        <g className="flower-illustration__plant">
          <path className="flower-illustration__root" d="M110 130c-1 11-6 18-14 24m15-17c7 4 11 10 13 17" />
          <path className="flower-illustration__stem" d={stage === 1 ? "M110 132C108 123 111 116 116 110" : stage === 2 ? "M110 132C109 111 110 88 111 66" : "M110 132C109 103 112 73 111 47"} />
          {stage === 1 ? <path className="flower-illustration__seed-shell" d="M93 125c2-15 11-24 24-24 12 0 21 9 22 21-10-4-18-2-23 8-8-8-15-10-23-5Z" /> : null}
          {stage === 1 ? (
            <g className="flower-illustration__cotyledons">
              <path className="flower-illustration__leaf" d="M115 111C102 99 93 103 94 108c1 7 9 10 21 9Z" />
              <path className="flower-illustration__leaf" d="M116 110c12-12 22-8 21-3-1 7-9 11-21 10Z" />
            </g>
          ) : null}
          {stage >= 2 ? (
            <>
              <path className="flower-illustration__leaf flower-illustration__leaf--left" d="M109 100C91 78 73 83 72 88c-1 10 16 21 37 18Z" />
              <path className="flower-illustration__leaf flower-illustration__leaf--right" d="M111 84c16-20 34-15 35-10 2 10-14 21-35 18Z" />
              <path className="flower-illustration__leaf-line flower-illustration__leaf-line--left" d="M105 101 80 89" />
              <path className="flower-illustration__leaf-line flower-illustration__leaf-line--right" d="m115 87 23-11" />
            </>
          ) : null}
          {stage === 2 ? (
            <g className="flower-illustration__new-leaves">
              <path className="flower-illustration__leaf" d="M111 67c-13-11-20-5-20-1 0 7 8 12 20 10Z" />
              <path className="flower-illustration__leaf" d="M112 67c12-11 20-5 20-1 0 7-8 12-20 10Z" />
            </g>
          ) : null}
          {stage === 3 ? (
            <g className="flower-illustration__bud" filter="url(#bloom-shadow)">
              <path className="flower-illustration__sepal" d="M96 58c5 10 23 10 30 0l-15 25Z" />
              <path className="flower-illustration__bud-petal" d="M111 24c17 9 22 24 11 37-7 8-16 8-23 0-11-13-5-29 12-37Z" />
              <path className="flower-illustration__bud-fold" d="M111 30c-6 12-5 21 3 30" />
            </g>
          ) : null}
          {stage >= 4 ? (
            <g className="flower-illustration__flower" filter="url(#bloom-shadow)">
              <ellipse className="flower-illustration__petal flower-illustration__petal--1" cx="111" cy="34" rx="18" ry="29" />
              <ellipse className="flower-illustration__petal flower-illustration__petal--2" cx="139" cy="49" rx="18" ry="29" transform="rotate(58 139 49)" />
              <ellipse className="flower-illustration__petal flower-illustration__petal--3" cx="132" cy="78" rx="18" ry="29" transform="rotate(126 132 78)" />
              <ellipse className="flower-illustration__petal flower-illustration__petal--4" cx="91" cy="78" rx="18" ry="29" transform="rotate(-126 91 78)" />
              <ellipse className="flower-illustration__petal flower-illustration__petal--5" cx="83" cy="49" rx="18" ry="29" transform="rotate(-58 83 49)" />
              <circle className="flower-illustration__center" cx="111" cy="59" r="15" />
              <circle className="flower-illustration__center-light" cx="106" cy="54" r="4" />
            </g>
          ) : null}
        </g>
      ) : null}
    </svg>
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
  const progress = Math.min(100, Math.round((state.days_grown / Math.max(state.days_in_month, 1)) * 100));
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
        <small>{state.days_grown} из {state.days_in_month} дней</small>
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
