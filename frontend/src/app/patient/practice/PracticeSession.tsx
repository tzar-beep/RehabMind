"use client";

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
import { Button, buttonClasses } from "@/components/ui/Button";
import { TextField } from "@/components/ui/TextField";
import { ApiError, apiFetch } from "@/lib/api/client";
import {
  ResponseResultSchema,
  SessionStateSchema,
  type Exercise,
  type Outcome,
  type ResponseResult,
  type SessionState,
} from "@/lib/api/schemas";

import { EMPTY_ANSWER, IMAGE_ALT, TYPE_HINT, feedbackFor } from "./messages";
import { SpeechRecorder, speechSupported } from "./SpeechRecorder";
import { WordBank } from "./WordBank";

type View =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "answering"; state: SessionState }
  | {
      kind: "feedback";
      exerciseType: string;
      matched: string[];
      missing: string[];
      outcome: Outcome;
      target: string;
      heard: string | null;
      imageUrl: string | null;
      next: SessionState;
    };

/** One picture, one question, one primary action at a time. */
export function PracticeSession() {
  const router = useRouter();
  const [view, setView] = useState<View>({ kind: "loading" });
  const [busy, setBusy] = useState(false);
  const [answerError, setAnswerError] = useState<string | null>(null);
  const [typing, setTyping] = useState(false);
  // Hints revealed for the current exercise (keyed so a new exercise starts at zero).
  const [hintState, setHintState] = useState({ exerciseId: "", count: 0 });
  const currentId =
    view.kind === "answering" ? view.state.exercise?.id : undefined;
  const hints = hintState.exerciseId === currentId ? hintState.count : 0;
  const [micNotice, setMicNotice] = useState<string | null>(null);
  const shownAt = useRef(0);
  const nextButton = useRef<HTMLButtonElement>(null);

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
    if (view.kind === "answering") shownAt.current = performance.now();
    if (view.kind === "feedback") nextButton.current?.focus();
  }, [view]);

  function showFeedback(exercise: Exercise, result: ResponseResult) {
    setView({
      kind: "feedback",
      exerciseType: exercise.type,
      matched: result.concepts_matched ?? [],
      missing: result.concepts_missing ?? [],
      outcome: result.outcome,
      target: result.target,
      heard: result.heard ?? null,
      imageUrl: exercise.image_url,
      next: result.state,
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
    return (
      <p className="text-xl text-ink-muted" role="status">
        Getting your practice ready…
      </p>
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
    const done = view.next.exercise === null;
    return (
      <div className="flex flex-col items-center gap-8 text-center">
        <div role="status" className="flex flex-col items-center gap-4">
          <p className="text-3xl font-bold">{fb.title}</p>
          {view.imageUrl && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={view.imageUrl}
              alt=""
              width={200}
              height={200}
              className="max-h-56 w-auto rounded-card border border-line bg-surface object-contain p-2"
            />
          )}
          <p className="text-xl text-ink-muted">{fb.lead}</p>
          <p
            className={`font-bold text-accent ${isWord ? "text-5xl" : "text-3xl"}`}
          >
            {view.target}
          </p>
          {view.exerciseType === "picture_description" && (
            <div className="flex flex-col gap-1 text-lg">
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
        <Button
          ref={nextButton}
          size="lg"
          onClick={() => setView({ kind: "answering", state: view.next })}
        >
          {done ? "See how you did" : "Next picture"}
        </Button>
      </div>
    );
  }

  const { state } = view;

  if (!state.exercise) {
    const s = state.summary;
    return (
      <div className="flex flex-col items-center gap-6 text-center">
        {s && <CompletionRing done={s.practiced} total={state.total} />}
        <h1 className="text-4xl font-bold">Practice complete</h1>
        {s && (
          <p className="text-2xl">
            You practised {s.practiced}{" "}
            {s.practiced === 1 ? "picture" : "pictures"}.
            {s.correct > 0 && ` You got ${s.correct} right on your own.`}
          </p>
        )}
        <p className="text-xl text-ink-muted">
          Well done for showing up today.
        </p>
        <Link href="/patient" className={buttonClasses("primary", "lg")}>
          Back to home
        </Link>
      </div>
    );
  }

  const ex = state.exercise;
  const canSpeak =
    ex.response_modes.includes("speech") && speechSupported() && !micNotice;
  const isSentence = ex.type === "sentence_construction";
  // Sentence building is tap-first; speech is used when typing/tapping is not allowed.
  const useSpeech =
    canSpeak && !typing && (!isSentence || !ex.response_modes.includes("text"));
  const isPhoto = ex.image_kind === "photo";
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
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between gap-4">
        <p className="text-lg text-ink-muted">
          Picture {ex.position} of {state.total}
        </p>
        <Button variant="quiet" onClick={stopForToday}>
          Stop for today
        </Button>
      </div>
      <div
        role="progressbar"
        aria-label="Practice progress"
        aria-valuemin={0}
        aria-valuemax={state.total}
        aria-valuenow={ex.position - 1}
        aria-valuetext={`${ex.position - 1} of ${state.total} pictures done`}
        className="flex gap-1.5"
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

      <section
        aria-labelledby="prompt"
        className="flex flex-col items-center gap-6"
      >
        {ex.image_url && (
          // Alt text must not name the object: that would give the answer away.
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={ex.image_url}
            alt={IMAGE_ALT[ex.type] ?? IMAGE_ALT.picture_naming}
            width={isPhoto ? 480 : 240}
            height={isPhoto ? 360 : 240}
            className={
              isPhoto
                ? "max-h-80 w-auto max-w-full rounded-card border border-line bg-surface object-contain"
                : "rounded-card border border-line bg-surface p-8"
            }
          />
        )}
        <h1 id="prompt" className="text-4xl font-bold">
          {ex.prompt}
        </h1>
      </section>

      {ex.cues.length > 0 && (
        <div className="flex flex-col items-center gap-3">
          {hints > 0 && (
            <div
              role="status"
              className="w-full rounded-card bg-accent-soft px-6 py-4"
            >
              <ul className="flex flex-col gap-2 text-xl">
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

      {useSpeech ? (
        <div className="flex flex-col gap-6">
          <p className="text-center text-lg text-ink-muted">
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
              setTyping(true);
            }}
          />
          <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
            <Button
              variant="secondary"
              size="lg"
              onClick={() => setTyping(true)}
            >
              {isSentence ? "Tap words instead" : "Type instead"}
            </Button>
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
            <Button variant="quiet" onClick={() => setTyping(false)}>
              Speak instead
            </Button>
          )}
        </>
      ) : (
        <form
          key={ex.id}
          onSubmit={onSubmit}
          noValidate
          className="flex flex-col gap-5"
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
          <div className="flex flex-col gap-3 sm:flex-row">
            <Button type="submit" size="lg" busy={busy} className="sm:flex-1">
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
            <Button variant="quiet" onClick={() => setTyping(false)}>
              Speak instead
            </Button>
          )}
        </form>
      )}
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
      className="relative grid size-40 place-items-center"
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
