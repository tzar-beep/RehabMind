"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type FormEvent } from "react";

import { Alert } from "@/components/ui/Alert";
import { Button, buttonClasses } from "@/components/ui/Button";
import { TextField } from "@/components/ui/TextField";
import { ApiError, apiFetch } from "@/lib/api/client";
import {
  ResponseResultSchema,
  SessionStateSchema,
  type Exercise,
  type Outcome,
  type SessionState,
} from "@/lib/api/schemas";

import { FEEDBACK } from "./messages";

type View =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "answering"; state: SessionState }
  | {
      kind: "feedback";
      outcome: Outcome;
      target: string;
      imageUrl: string | null;
      next: SessionState;
    };

/** One picture, one question, one primary action at a time. */
export function PracticeSession() {
  const router = useRouter();
  const [view, setView] = useState<View>({ kind: "loading" });
  const [busy, setBusy] = useState(false);
  const [answerError, setAnswerError] = useState<string | null>(null);
  const shownAt = useRef(0);
  const nextButton = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    apiFetch("/practice/sessions", { method: "POST" }, SessionStateSchema)
      .then((state) => setView({ kind: "answering", state: state! }))
      .catch((e) =>
        setView({ kind: "error", message: e instanceof ApiError ? e.message : String(e) }),
      );
  }, []);

  useEffect(() => {
    if (view.kind === "answering") shownAt.current = performance.now();
    if (view.kind === "feedback") nextButton.current?.focus();
  }, [view]);

  async function submit(exercise: Exercise, body: { text?: string; skipped?: boolean }) {
    setBusy(true);
    setAnswerError(null);
    try {
      const result = await apiFetch(
        `/practice/exercises/${exercise.id}/responses`,
        {
          method: "POST",
          json: { ...body, latency_ms: Math.round(performance.now() - shownAt.current) },
        },
        ResponseResultSchema,
      );
      setView({
        kind: "feedback",
        outcome: result!.outcome,
        target: result!.target,
        imageUrl: exercise.image_url,
        next: result!.state,
      });
    } catch (e) {
      setAnswerError(e instanceof ApiError ? e.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  async function stopForToday() {
    await apiFetch("/practice/sessions/current/end", { method: "POST" }).catch(() => undefined);
    router.replace("/patient");
    router.refresh();
  }

  if (view.kind === "loading") {
    return <p className="text-xl text-ink-muted" role="status">Getting your practice ready…</p>;
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
    const fb = FEEDBACK[view.outcome];
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
              className="rounded-card border border-line bg-surface p-6"
            />
          )}
          <p className="text-xl text-ink-muted">{fb.lead}</p>
          <p className="text-5xl font-bold text-accent">{view.target}</p>
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
        <h1 className="text-4xl font-bold">Practice complete</h1>
        {s && (
          <p className="text-2xl">
            You practised {s.practiced} {s.practiced === 1 ? "picture" : "pictures"}.
            {s.correct > 0 && ` You named ${s.correct} on your own.`}
          </p>
        )}
        <p className="text-xl text-ink-muted">Well done for showing up today.</p>
        <Link href="/patient" className={buttonClasses("primary", "lg")}>
          Back to home
        </Link>
      </div>
    );
  }

  const ex = state.exercise;

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = String(new FormData(event.currentTarget).get("answer") ?? "").trim();
    if (!text) {
      setAnswerError("Type a word, or choose “I’m not sure”.");
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
        aria-hidden="true"
        className="h-2 w-full overflow-hidden rounded-full bg-line"
      >
        <div
          className="h-full rounded-full bg-accent"
          style={{ width: `${((ex.position - 1) / state.total) * 100}%` }}
        />
      </div>

      <section aria-labelledby="prompt" className="flex flex-col items-center gap-6">
        {ex.image_url && (
          // Alt text must not name the object: that would give the answer away.
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={ex.image_url}
            alt="Picture to name"
            width={240}
            height={240}
            className="rounded-card border border-line bg-surface p-8"
          />
        )}
        <h1 id="prompt" className="text-4xl font-bold">
          {ex.prompt}
        </h1>
      </section>

      <form key={ex.id} onSubmit={onSubmit} noValidate className="flex flex-col gap-5">
        <TextField
          label="Your answer"
          hint={ex.instructions}
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
      </form>
    </div>
  );
}
