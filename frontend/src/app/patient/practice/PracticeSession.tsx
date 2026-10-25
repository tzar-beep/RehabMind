"use client";

import {
  CircleCheck,
  HeartHandshake,
  Lightbulb,
  Coffee,
  Sparkles,
  Volume2,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type FormEvent,
} from "react";

import { Alert } from "@/components/ui/Alert";
import { LoadingRegion, Skeleton } from "@/components/ui/Skeleton";
import { Button, buttonClasses } from "@/components/ui/Button";
import { TextField } from "@/components/ui/TextField";
import { ApiError, apiFetch } from "@/lib/api/client";
import {
  RecapSchema,
  ResponseResultSchema,
  SessionStateSchema,
  type Exercise,
  type RecapWord,
  type Outcome,
  type ResponseResult,
  type SessionState,
} from "@/lib/api/schemas";

import { AiTip } from "./AiTip";
import { ChoiceGrid, WordCard, say, useCanSpeak } from "./Choices";
import { DifficultyRating } from "./DifficultyRating";
import { EMPTY_ANSWER, IMAGE_ALT, TYPE_HINT, feedbackFor } from "./messages";
import { SpeechRecorder, speechSupported } from "./SpeechRecorder";
import { WordBank } from "./WordBank";

const MISSES_FOR_BREAK = 4;

const AI_TIP_TYPES = new Set([
  "picture_naming",
  "sentence_construction",
  "picture_description",
]);

type View =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "answering"; state: SessionState }
  | {
      kind: "feedback";
      exerciseId: string;
      exerciseType: string;
      matched: string[];
      missing: string[];
      outcome: Outcome;
      target: string;
      heard: string | null;
      imageUrl: string | null;
      /** The answer was the session's last picture. */
      last: boolean;
    };

/** One picture, one question, one primary action at a time. */
export function PracticeSession() {
  const router = useRouter();
  const [view, setView] = useState<View>({ kind: "loading" });
  const [busy, setBusy] = useState(false);
  // Misses or skips in a row in this visit; enough of them and a break is offered (once).
  const [misses, setMisses] = useState(0);
  const [breakOffered, setBreakOffered] = useState(false);
  const [answerError, setAnswerError] = useState<string | null>(null);
  // How the patient answers: the default for the exercise type, or their explicit choice.
  // The choice carries over to later exercises in the session.
  const [inputMode, setInputMode] = useState<"auto" | "speech" | "manual">(
    "auto",
  );
  // Hints revealed for the current exercise (keyed so a new exercise starts at zero).
  const [hintState, setHintState] = useState({ exerciseId: "", count: 0 });
  const currentId =
    view.kind === "answering" ? view.state.exercise?.id : undefined;
  const hints = hintState.exerciseId === currentId ? hintState.count : 0;
  const [micNotice, setMicNotice] = useState<string | null>(null);
  const shownAt = useRef(0);
  const nextButton = useRef<HTMLButtonElement>(null);
  // The next exercise, fetched while the patient reads their feedback.
  const nextState = useRef<Promise<SessionState | undefined> | null>(null);

  useEffect(() => {
    apiFetch("/practice/sessions", { method: "POST" }, SessionStateSchema)
      .then((state) => setView({ kind: "answering", state: state! }))
      .catch((e) =>
        setView({
          kind: "error",
          message: e instanceof ApiError ? e.message : String(e),
        }),
      );
  }, []);

  useEffect(() => {
    // Each picture, result and summary starts at the top of the page.
    window.scrollTo({ top: 0 });
    if (view.kind === "answering") shownAt.current = performance.now();
    if (view.kind === "feedback")
      nextButton.current?.focus({ preventScroll: true });
  }, [view]);

  function showFeedback(exercise: Exercise, result: ResponseResult) {
    setMisses((m) => (result.outcome === "correct" ? 0 : m + 1));
    // Answers are scored at once; the next exercise is prepared in the background (the
    // server issues it on this request), so "Next picture" rarely has to wait.
    nextState.current =
      result.state.exercise || result.state.status !== "active"
        ? Promise.resolve(result.state)
        : apiFetch(
            "/practice/sessions",
            { method: "POST" },
            SessionStateSchema,
          );
    nextState.current.catch(() => undefined);
    setView({
      kind: "feedback",
      exerciseId: exercise.id,
      exerciseType: exercise.type,
      matched: result.concepts_matched ?? [],
      missing: result.concepts_missing ?? [],
      outcome: result.outcome,
      target: result.target,
      heard: result.heard ?? null,
      // Picture choices have no single picture: show the one that was right.
      imageUrl:
        exercise.image_url ??
        exercise.options?.find((o) => o.word === result.target)?.image_url ??
        null,
      last: exercise.position >= result.state.total,
    });
  }

  async function submit(
    exercise: Exercise,
    body: { text?: string; skipped?: boolean },
  ) {
    setBusy(true);
    setAnswerError(null);
    try {
      const result = await apiFetch(
        `/practice/exercises/${exercise.id}/responses`,
        {
          method: "POST",
          json: {
            ...body,
            hints_used: hints,
            latency_ms: Math.round(performance.now() - shownAt.current),
            defer_next: true,
          },
        },
        ResponseResultSchema,
      );
      showFeedback(exercise, result!);
    } catch (e) {
      setAnswerError(
        e instanceof ApiError
          ? e.message
          : "Something went wrong. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function stopForToday() {
    await apiFetch("/practice/sessions/current/end", { method: "POST" }).catch(
      () => undefined,
    );
    router.replace("/patient");
    router.refresh();
  }

  if (view.kind === "loading") {
    // Same shape as the exercise screen, so nothing jumps when it appears.
    return (
      <LoadingRegion label="Getting your practice ready…" className="gap-8">
        <h1 className="sr-only">Practice</h1>
        <div className="flex items-center justify-between">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-6 w-28" />
        </div>
        <Skeleton className="h-3 rounded-full" />
        <Skeleton className="mx-auto h-72 w-full max-w-md rounded-card" />
        <Skeleton className="mx-auto h-10 w-64" />
        <div className="flex flex-col gap-3 sm:flex-row">
          <Skeleton className="h-16 sm:flex-1" />
          <Skeleton className="h-16 sm:w-48" />
        </div>
        <p aria-hidden="true" className="text-center text-lg text-ink-muted">
          Getting your practice ready…
        </p>
      </LoadingRegion>
    );
  }

  if (view.kind === "error") {
    return (
      <div className="flex flex-col gap-6">
        <Alert tone="error">{view.message}</Alert>
        <Link href="/patient" className={buttonClasses("secondary", "lg")}>
          Back to home
        </Link>
      </div>
    );
  }

  if (view.kind === "feedback") {
    const fb = feedbackFor(view.exerciseType, view.outcome);
    const isWord = view.exerciseType === "picture_naming";
    const done = view.last;
    // After a run of misses the break suggestion is the message; the tip steps aside.
    const offerBreak = misses >= MISSES_FOR_BREAK && !breakOffered && !done;
    // Two columns on wide screens (picture | result), so "Next picture" stays in view
    // even with a tip; one centred column on phones.
    return (
      <div className="flex min-h-0 flex-1 flex-col items-center gap-4 rounded-card border border-line bg-surface px-5 py-5 text-center shadow-card sm:gap-5 sm:py-8 lg:grid lg:grid-cols-2 lg:grid-rows-[minmax(0,1fr)] lg:gap-10 lg:px-10 lg:text-left short:gap-3 short:sm:py-4">
        {view.imageUrl && (
          <div className="relative min-h-16 w-full max-w-md flex-1 lg:h-full lg:max-w-none">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={view.imageUrl}
              alt=""
              width={200}
              height={200}
              className="absolute inset-0 size-full rounded-card border border-line bg-surface object-contain p-2"
            />
          </div>
        )}
        <div
          className={`flex shrink-0 flex-col items-center gap-4 lg:items-start ${view.imageUrl ? "" : "lg:col-span-2"}`}
        >
          <div
            role="status"
            className="flex flex-col items-center gap-2 sm:gap-3 lg:items-start"
          >
            <div className="flex items-center gap-3">
              <OutcomeIcon outcome={view.outcome} />
              <p className="text-2xl font-bold sm:text-3xl">{fb.title}</p>
            </div>
            <p className="text-xl text-ink-muted">{fb.lead}</p>
            <div className="flex flex-wrap items-center justify-center gap-3 lg:justify-start">
              <p
                className={`font-bold text-accent ${isWord ? "text-4xl sm:text-5xl" : "text-2xl sm:text-3xl"}`}
              >
                {view.target}
              </p>
              {/* Hearing the word is itself a cue: listen, then say it to yourself. */}
              <HearIt text={view.target} />
            </div>
            {view.exerciseType === "picture_description" && (
              <div className="flex flex-col gap-1 text-lg short:text-base">
                {view.matched.length > 0 && (
                  <p>You mentioned: {view.matched.join(", ")}.</p>
                )}
                {view.missing.length > 0 && (
                  <p className="text-ink-muted">
                    You could also say: {view.missing.join(", ")}.
                  </p>
                )}
              </div>
            )}
            {view.heard && view.outcome !== "correct" && (
              <p className="text-lg text-ink-muted">
                We heard &ldquo;{view.heard}&rdquo;.
              </p>
            )}
          </div>
          {/* A tip after a close answer or a skip. Not after a different word: the model
            cannot reliably say what a word means (a walkthrough found "something you use
            for writing notes" for key), and the word with Hear it is the better cue. Only
            the types the AI personalises (backend AI_TYPES) were audited for tips. */}
          {(view.outcome === "near_miss" || view.outcome === "skipped") &&
            AI_TIP_TYPES.has(view.exerciseType) &&
            !offerBreak && (
              <AiTip key={view.exerciseId} exerciseId={view.exerciseId} />
            )}
          <Button
            ref={nextButton}
            size="lg"
            busy={busy}
            onClick={async () => {
              setBusy(true);
              try {
                if (misses >= MISSES_FOR_BREAK) setBreakOffered(true);
                const next = await nextState.current;
                setView({ kind: "answering", state: next! });
              } catch (e) {
                setView({
                  kind: "error",
                  message: e instanceof ApiError ? e.message : String(e),
                });
              } finally {
                setBusy(false);
              }
            }}
          >
            {done ? "See how you did" : "Next picture"}
          </Button>
          {/* Fatigue shows as a run of misses: offer a break, never insist. */}
          {offerBreak && (
            <div
              role="status"
              className="flex w-full max-w-xl flex-wrap items-center justify-between gap-3 rounded-card border border-line bg-canvas px-4 py-3 text-left"
            >
              <span className="flex items-center gap-2 text-lg">
                <Coffee aria-hidden="true" size={20} className="text-accent" />
                That was a few tricky ones. A short break often helps.
              </span>
              <Button
                variant="secondary"
                onClick={() => {
                  setBreakOffered(true);
                  void stopForToday();
                }}
              >
                Take a break
              </Button>
            </div>
          )}
        </div>
      </div>
    );
  }

  const { state } = view;

  if (!state.exercise) {
    const s = state.summary;
    const practised = !!s && s.practiced > 0;
    // One screen: the summary and the way home on the left, the patient's words and the
    // rating on the right (stacked on phones).
    return (
      <div className="flex min-h-0 flex-1 flex-col items-center justify-center gap-4 rounded-card border border-line bg-surface px-5 py-5 text-center shadow-card sm:gap-6 sm:py-8 lg:grid lg:grid-cols-2 lg:gap-10 lg:px-10">
        <div className="flex flex-col items-center gap-3 sm:gap-4">
          {/* On a phone the sentence below says the same; the ring would cost a third
              of the screen. */}
          {s && (
            <div className="max-lg:hidden">
              <CompletionRing done={s.practiced} total={state.total} />
            </div>
          )}
          <h1 className="text-3xl font-bold sm:text-4xl">Practice complete</h1>
          {s && (
            <p className="text-xl sm:text-2xl">
              You practised {s.practiced}{" "}
              {s.practiced === 1 ? "picture" : "pictures"}.
              {s.correct > 0 && ` You got ${s.correct} right on your own.`}
            </p>
          )}
          <p className="text-lg text-ink-muted max-sm:hidden sm:text-xl">
            Well done for showing up today.
          </p>
          <Link
            href="/patient"
            className={`${buttonClasses("primary", "lg")} max-lg:order-last`}
          >
            Back to home
          </Link>
        </div>
        {practised && (
          <div className="flex w-full flex-col items-center gap-4 sm:gap-6">
            <SessionRecap sessionId={state.session_id} />
            <DifficultyRating sessionId={state.session_id} />
          </div>
        )}
      </div>
    );
  }

  const ex = state.exercise;
  const canSpeak =
    ex.response_modes.includes("speech") && speechSupported() && !micNotice;
  const isSentence = ex.type === "sentence_construction";
  // Sentence building is tap-first by default; speech is used when the patient asks for
  // it, or when typing/tapping is not allowed.
  const useSpeech =
    canSpeak &&
    (inputMode === "speech" ||
      (inputMode === "auto" &&
        (!isSentence || !ex.response_modes.includes("text"))));
  const isPhoto = ex.image_kind === "photo";
  const options = ex.options ?? [];
  const isChoice = options.length > 0;
  if (!ex.response_modes.includes("text") && !canSpeak) {
    return (
      <Alert tone="error">
        Speaking isn&rsquo;t available on this device. Please contact your care
        team.
      </Alert>
    );
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = String(
      new FormData(event.currentTarget).get("answer") ?? "",
    ).trim();
    if (!text) {
      setAnswerError(EMPTY_ANSWER[ex.type] ?? EMPTY_ANSWER.picture_naming);
      return;
    }
    void submit(ex, { text });
  }

  return (
    // One screen: a slim top row, then the picture takes whatever height is left.
    <div className="flex min-h-0 flex-1 flex-col gap-3 sm:gap-5">
      <div className="flex shrink-0 items-center gap-3 sm:gap-5">
        <p className="shrink-0 text-lg text-ink-muted">
          Picture {ex.position} of {state.total}
        </p>
        <div
          role="progressbar"
          aria-label="Practice progress"
          aria-valuemin={0}
          aria-valuemax={state.total}
          aria-valuenow={ex.position - 1}
          aria-valuetext={`${ex.position - 1} of ${state.total} pictures done`}
          className="flex min-w-0 flex-1 gap-1.5"
        >
          {Array.from({ length: state.total }, (_, i) => (
            <span
              key={i}
              className={
                "h-3 flex-1 rounded-full transition-colors " +
                (i < ex.position - 1
                  ? "bg-accent"
                  : i === ex.position - 1
                    ? "bg-accent/35"
                    : "bg-line")
              }
            />
          ))}
        </div>
        <Button variant="quiet" className="shrink-0" onClick={stopForToday}>
          Stop for today
        </Button>
      </div>

      {/* Picture beside the question and answer on wide screens; above them on phones,
          shrinking to the space that is left. */}
      <section
        aria-labelledby="prompt"
        className="flex min-h-0 flex-1 flex-col gap-4 lg:grid lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] lg:grid-rows-[minmax(0,1fr)] lg:items-center lg:gap-12"
      >
        <div
          className={
            isChoice
              ? "relative order-last min-h-0 lg:order-none lg:h-full"
              : "relative min-h-16 flex-1 lg:h-full"
          }
        >
          {isChoice && (
            // Wide screens: a square as tall as the space, placed absolutely so its size
            // can never push the page taller (an aspect ratio sized from the width did).
            <div className="flex flex-col gap-4 lg:absolute lg:inset-y-0 lg:left-1/2 lg:aspect-square lg:max-w-full lg:-translate-x-1/2">
              <ChoiceGrid
                options={options}
                busy={busy}
                onPick={(word) => void submit(ex, { text: word })}
              />
              {/* On a phone the choices come first, then the way out. */}
              <Button
                variant="secondary"
                size="lg"
                disabled={busy}
                className="lg:hidden"
                onClick={() => submit(ex, { skipped: true })}
              >
                I&rsquo;m not sure
              </Button>
            </div>
          )}
          {!isChoice && ex.image_url && (
            // Alt text must not name the object: that would give the answer away.
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={ex.image_url}
              alt={IMAGE_ALT[ex.type] ?? IMAGE_ALT.picture_naming}
              width={isPhoto ? 480 : 240}
              height={isPhoto ? 360 : 240}
              className={
                // Absolutely placed in the space left, so it can never push anything off screen.
                isPhoto
                  ? "absolute inset-0 size-full rounded-card bg-surface object-contain p-2"
                  : "absolute inset-0 size-full rounded-card border border-line bg-surface object-contain p-6"
              }
            />
          )}
        </div>
        <div className="flex shrink-0 flex-col gap-3 sm:gap-4 short:gap-2.5">
          <div className="flex items-start justify-center gap-3 lg:justify-start">
            <h1
              id="prompt"
              className="text-center text-2xl font-bold tracking-tight sm:text-3xl lg:text-left lg:text-4xl short:lg:text-2xl"
            >
              {ex.prompt}
            </h1>
            <HearQuestion text={ex.prompt} />
          </div>
          {ex.word && (
            <WordCard
              key={ex.id}
              word={ex.word}
              listenFirst={ex.type === "word_repetition" && !useSpeech}
            />
          )}

          {ex.cues.length > 0 && (
            <div className="flex flex-col items-center gap-3 lg:items-start">
              {hints > 0 && (
                <div
                  role="status"
                  className="flex w-full gap-3 rounded-card border border-accent/20 bg-accent-soft px-4 py-3"
                >
                  <span
                    aria-hidden="true"
                    className="grid size-11 shrink-0 place-items-center rounded-full bg-surface text-warning"
                  >
                    <Lightbulb size={22} />
                  </span>
                  <ul className="flex flex-col gap-1 self-center text-lg sm:text-xl">
                    {ex.cues.slice(0, hints).map((cue) => (
                      <li key={cue}>
                        <Cue text={cue} />
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {hints < ex.cues.length && (
                <Button
                  variant="quiet"
                  onClick={() =>
                    setHintState({ exerciseId: ex.id, count: hints + 1 })
                  }
                >
                  {hints === 0 ? "Show a hint" : "Show another hint"}
                </Button>
              )}
            </div>
          )}

          {micNotice && <Alert tone="info">{micNotice}</Alert>}

          {isChoice ? (
            <div className="hidden flex-col gap-3 lg:flex lg:items-start">
              {answerError && <Alert tone="error">{answerError}</Alert>}
              <Button
                variant="secondary"
                size="lg"
                disabled={busy}
                onClick={() => submit(ex, { skipped: true })}
              >
                I&rsquo;m not sure
              </Button>
            </div>
          ) : useSpeech ? (
            <div className="flex flex-col gap-3 sm:gap-5">
              <p className="hidden text-center text-lg text-ink-muted sm:block lg:text-left short:hidden">
                {ex.instructions}
              </p>
              <SpeechRecorder
                key={ex.id}
                exerciseId={ex.id}
                hintsUsed={hints}
                latencyMs={() => performance.now() - shownAt.current}
                onResult={(result) => showFeedback(ex, result)}
                onUnavailable={(message) => {
                  setMicNotice(message);
                  setInputMode("manual");
                }}
              />
              <div className="grid grid-cols-2 gap-3 sm:flex sm:justify-center lg:justify-start">
                {ex.response_modes.includes("text") && (
                  <Button
                    variant="secondary"
                    size="lg"
                    onClick={() => setInputMode("manual")}
                  >
                    {isSentence ? "Tap words instead" : "Type instead"}
                  </Button>
                )}
                <Button
                  variant="secondary"
                  size="lg"
                  onClick={() => submit(ex, { skipped: true })}
                >
                  I&rsquo;m not sure
                </Button>
              </div>
            </div>
          ) : isSentence && ex.words ? (
            <>
              <WordBank
                key={ex.id}
                words={ex.words}
                busy={busy}
                error={answerError}
                onCheck={(sentence) =>
                  sentence
                    ? void submit(ex, { text: sentence })
                    : setAnswerError(EMPTY_ANSWER.sentence_construction)
                }
                onSkip={() => submit(ex, { skipped: true })}
              />
              {canSpeak && (
                <Button variant="quiet" onClick={() => setInputMode("speech")}>
                  Speak instead
                </Button>
              )}
            </>
          ) : (
            <form
              key={ex.id}
              onSubmit={onSubmit}
              noValidate
              className="flex flex-col gap-3 sm:gap-4"
            >
              <TextField
                label={
                  ex.type === "picture_description"
                    ? "Your description"
                    : "Your answer"
                }
                hint={TYPE_HINT[ex.type] ?? TYPE_HINT.picture_naming}
                name="answer"
                autoComplete="off"
                autoCapitalize="none"
                spellCheck={false}
                autoFocus
                error={answerError ?? undefined}
                className="text-2xl"
              />
              <div className="flex gap-3">
                <Button type="submit" size="lg" busy={busy} className="flex-1">
                  Check
                </Button>
                <Button
                  variant="secondary"
                  size="lg"
                  disabled={busy}
                  onClick={() => submit(ex, { skipped: true })}
                >
                  I&rsquo;m not sure
                </Button>
              </div>
              {canSpeak && (
                <Button variant="quiet" onClick={() => setInputMode("speech")}>
                  Speak instead
                </Button>
              )}
            </form>
          )}
        </div>
      </section>
    </div>
  );
}

/** Pictures practised out of planned. Always framed as progress, never as errors. */
function CompletionRing({ done, total }: { done: number; total: number }) {
  const r = 52;
  const length = 2 * Math.PI * r;
  const share = total > 0 ? Math.min(done / total, 1) : 0;
  return (
    // The sentence below the ring states the same number for assistive technology.
    <div
      aria-hidden="true"
      className="relative grid size-28 place-items-center sm:size-36 short:size-24"
    >
      <svg viewBox="0 0 120 120" className="absolute inset-0 -rotate-90">
        <circle
          cx="60"
          cy="60"
          r={r}
          fill="none"
          strokeWidth="10"
          className="stroke-accent-soft"
        />
        <circle
          cx="60"
          cy="60"
          r={r}
          fill="none"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={length}
          strokeDashoffset={length * (1 - share)}
          className="animate-ring-fill stroke-accent"
          style={{ "--ring-length": length } as CSSProperties}
        />
      </svg>
      <p className="flex flex-col items-center leading-tight">
        <span className="text-4xl font-bold tabular-nums">{done}</span>
        <span className="text-base text-ink-muted">
          {done === 1 ? "picture" : "pictures"}
        </span>
      </p>
    </div>
  );
}

/** Hint text with the quoted first sound ("It starts with “b…”") visually emphasised. */
function Cue({ text }: { text: string }) {
  const match = /“([^”…]+)…”/.exec(text);
  if (!match) return text;
  const before = text.slice(0, match.index);
  const after = text.slice(match.index + match[0].length);
  return (
    <>
      {`${before}“`}
      <strong className="rounded-md bg-surface px-1 text-accent-hover">
        {match[1]}
      </strong>
      {`…”${after}`}
    </>
  );
}

const OUTCOME_ICON = {
  correct: { Icon: CircleCheck, cls: "bg-success-soft text-success" },
  near_miss: { Icon: Sparkles, cls: "bg-accent-soft text-accent-hover" },
  incorrect: { Icon: HeartHandshake, cls: "bg-[#e5edf9] text-[#2f5ea8]" },
  skipped: { Icon: HeartHandshake, cls: "bg-[#e5edf9] text-[#2f5ea8]" },
} as const;

/** Friendly outcome icon; never red, so a missed word never feels like failure. */
function OutcomeIcon({ outcome }: { outcome: keyof typeof OUTCOME_ICON }) {
  const { Icon, cls } = OUTCOME_ICON[outcome];
  return (
    <span
      aria-hidden="true"
      className="relative grid size-12 shrink-0 place-items-center sm:size-14"
    >
      {/* The peak of each picture: naming it on your own gets one soft, expanding ring. */}
      {outcome === "correct" && (
        <span className="absolute inset-0 animate-ripple rounded-full bg-success" />
      )}
      <span
        className={`relative grid size-full animate-pop place-items-center rounded-full ${cls}`}
      >
        <Icon size={28} />
      </span>
    </span>
  );
}

/** Plays a word or sentence with the device's voice. */
function HearIt({ text }: { text: string }) {
  const speakable = useCanSpeak();
  if (!speakable) return null;
  return (
    <button
      type="button"
      onClick={() => say(text)}
      className="inline-flex min-h-target items-center gap-2 rounded-control border-2 border-accent px-4 font-bold text-accent transition-colors hover:bg-accent-soft"
    >
      <Volume2 aria-hidden="true" size={22} />
      Hear it
    </button>
  );
}

/** Reads the question aloud: reading is often harder than listening after a stroke. */
function HearQuestion({ text }: { text: string }) {
  const speakable = useCanSpeak();
  if (!speakable) return null;
  return (
    <button
      type="button"
      onClick={() => say(text.replace(/_{2,}/g, "blank"))}
      aria-label="Hear the question"
      title="Hear the question"
      className="inline-flex size-target shrink-0 items-center justify-center rounded-full border-2 border-line text-accent transition-colors hover:border-accent hover:bg-accent-soft sm:mt-1"
    >
      <Volume2 aria-hidden="true" size={22} />
    </button>
  );
}

/**
 * The end of the session is what is remembered (peak-end): show the words named today,
 * with their pictures. If none were named, show what was practised, never what was missed.
 */
// Six fit on one row beside the summary, and in two rows on a phone.
const RECAP_MAX = 6;

function SessionRecap({ sessionId }: { sessionId: string }) {
  // From the server, so answers given before a "Keep going" and by voice are included.
  const [words, setWords] = useState<RecapWord[] | null>(null);
  useEffect(() => {
    apiFetch(`/practice/sessions/${sessionId}/recap`, {}, RecapSchema)
      .then((w) => setWords(w ?? []))
      .catch(() => setWords([])); // the recap is a bonus: never block the ending
  }, [sessionId]);
  if (!words) return null;
  const named = words.filter((w) => w.outcome === "correct");
  const shown = (named.length ? named : words)
    .filter((w, i, all) => all.findIndex((x) => x.word === w.word) === i)
    .slice(0, RECAP_MAX);
  if (shown.length === 0) return null;
  return (
    <section
      aria-labelledby="recap-heading"
      className="flex w-full flex-col gap-3"
    >
      <h2 id="recap-heading" className="text-xl font-bold sm:text-2xl">
        {named.length ? "Words you named today" : "Words you practised today"}
      </h2>
      <ul className="flex flex-wrap justify-center gap-3 max-sm:[&>li:nth-child(n+4)]:hidden short:[&>li:nth-child(n+5)]:hidden">
        {shown.map((w, i) => (
          <li
            key={w.word}
            style={{ "--i": i } as CSSProperties}
            className="flex w-24 animate-rise flex-col items-center gap-1 rounded-card border border-line bg-surface p-2 [animation-delay:calc(var(--i)*80ms)]"
          >
            {w.image_url && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={w.image_url}
                alt=""
                width={96}
                height={96}
                className="size-16 object-contain max-sm:size-12 short:size-12"
              />
            )}
            <span lang="en" className="text-lg font-bold">
              {w.word}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
