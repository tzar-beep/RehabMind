"use client";

/** One visual per pipeline step, used on the presentation slides. All data is real. */

import {
  ArrowRight,
  Check,
  CircleX,
  Keyboard,
  Lightbulb,
  Mic,
  Repeat,
  X,
} from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { useEffect, useState } from "react";

import type { Pipeline, PipelineGeneration } from "@/lib/api/clinician";
import { cn } from "@/lib/utils";

type Trace = Pipeline["traces"][number];

/** Text that types itself out (instantly with reduced motion). Screen readers get it all. */
export function Typewriter({
  text,
  speed = 14,
  className,
}: {
  text: string;
  speed?: number;
  className?: string;
}) {
  const reduce = useReducedMotion();
  const [shown, setShown] = useState(0);
  useEffect(() => {
    if (reduce) return;
    const id = setInterval(
      () =>
        setShown((n) => {
          if (n >= text.length) {
            clearInterval(id);
            return n;
          }
          return n + 2;
        }),
      speed,
    );
    return () => clearInterval(id);
  }, [text, speed, reduce]);
  const visible = reduce ? text : text.slice(0, shown);
  return (
    <span className={className}>
      <span className="sr-only">{text}</span>
      <span aria-hidden="true">
        {visible}
        {!reduce && shown < text.length && (
          <span className="ml-0.5 inline-block h-[1em] w-2 animate-pulse bg-current align-[-2px]" />
        )}
      </span>
    </span>
  );
}

const rise = (i: number) => ({
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: {
    delay: 0.08 * i,
    duration: 0.35,
    ease: [0.2, 0.7, 0.2, 1] as const,
  },
});

function Pill({
  label,
  value,
  tone = "bg-canvas",
}: {
  label: string;
  value: string;
  tone?: string;
}) {
  return (
    <div className={cn("flex flex-col rounded-2xl px-4 py-3", tone)}>
      <span className="text-sm text-ink-muted">{label}</span>
      <span className="text-xl font-bold tabular-nums">{value}</span>
    </div>
  );
}

const OUTCOME_DOT: Record<string, string> = {
  correct: "bg-success",
  near_miss: "bg-[#c27c2c]",
  incorrect: "bg-[#8a8378]",
  skipped: "bg-line-strong",
};

// ---------- 1. ML ability ----------
export function AbilityVisual({ ctx }: { ctx: Record<string, unknown> }) {
  const theta = Number(ctx.ability ?? 0);
  const pos = Math.min(100, Math.max(0, ((theta + 4) / 8) * 100));
  const outcomes = (ctx.recent_outcomes as string[] | undefined) ?? [];
  const acc = ctx.recent_accuracy as number | null | undefined;
  const pred = ctx.predicted_success as number | null | undefined;
  return (
    <div className="flex flex-col gap-5">
      <div>
        <div className="mb-2 flex justify-between text-sm text-ink-muted">
          <span>Finding it hard</span>
          <span>Learned ability θ = {theta.toFixed(2)}</span>
          <span>Doing well</span>
        </div>
        <div className="relative h-4 rounded-full bg-linear-to-r from-[#e9b8a8] via-[#f3d9a4] to-[#9fd8c4]">
          <motion.span
            aria-hidden="true"
            initial={{ left: "50%" }}
            animate={{ left: `${pos}%` }}
            transition={{ type: "spring", stiffness: 80, damping: 14 }}
            className="absolute top-1/2 size-7 -translate-x-1/2 -translate-y-1/2 rounded-full border-4 border-white bg-brand-deep shadow-lg"
          />
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm text-ink-muted">Last answers:</span>
        {outcomes.length === 0 && <span className="text-sm">none yet</span>}
        {outcomes.map((o, i) => (
          <motion.span
            key={i}
            {...rise(i)}
            title={o}
            className={cn("size-4 rounded-full", OUTCOME_DOT[o] ?? "bg-line")}
          />
        ))}
      </div>
      <div className="grid grid-cols-3 gap-3">
        <Pill
          label="Recent accuracy"
          value={acc == null ? "—" : `${Math.round(acc * 100)}%`}
        />
        <Pill
          label="Predicted success"
          value={pred == null ? "—" : `${Math.round(pred * 100)}%`}
          tone="bg-[#f1eaf7]"
        />
        <Pill
          label="Trend"
          value={String(ctx.trend ?? "—").replaceAll("_", " ")}
        />
      </div>
    </div>
  );
}

// ---------- 2. structured context ----------
export function ContextVisual({ ctx }: { ctx: Record<string, unknown> }) {
  const min = Number(ctx.min_difficulty ?? 1);
  const max = Number(ctx.max_difficulty ?? 5);
  const target = Number(ctx.target_difficulty ?? min);
  const candidates = (ctx.candidates as { slug: string }[] | undefined) ?? [];
  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <motion.div {...rise(0)} className="rounded-2xl bg-accent-soft p-4">
          <p className="text-sm text-ink-muted">Objective</p>
          <p className="text-lg font-bold">
            {String(ctx.objective_label ?? "")}
          </p>
          <p className="text-sm">{String(ctx.target_skill ?? "")}</p>
        </motion.div>
        <motion.div {...rise(1)} className="rounded-2xl bg-[#e5edf9] p-4">
          <p className="text-sm text-ink-muted">
            Difficulty (fixed by the app)
          </p>
          <div className="mt-2 flex gap-1.5" aria-hidden="true">
            {[1, 2, 3, 4, 5].map((d) => (
              <span
                key={d}
                className={cn(
                  "grid h-8 flex-1 place-items-center rounded-lg text-sm font-bold",
                  d === target
                    ? "bg-[#2f5ea8] text-white"
                    : d >= min && d <= max
                      ? "bg-white text-[#2f5ea8]"
                      : "bg-white/40 text-ink-muted",
                )}
              >
                {d}
              </span>
            ))}
          </div>
          <p className="mt-2 text-sm">
            Level {target}; the clinician allows {min} to {max}
          </p>
        </motion.div>
      </div>
      <motion.div {...rise(2)} className="rounded-2xl bg-canvas p-4">
        <p className="text-sm text-ink-muted">
          {candidates.length} approved pictures the model may choose from
        </p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {candidates.slice(0, 8).map((c) => (
            <span
              key={c.slug}
              className="rounded-full bg-surface px-3 py-1 font-mono text-xs ring-1 ring-line"
            >
              {c.slug.replace("photo_", "")}
            </span>
          ))}
        </div>
      </motion.div>
      <motion.p {...rise(3)} className="text-sm text-ink-muted">
        Weakness: {String(ctx.weakness ?? "none")} · no names, emails or IDs are
        sent.
      </motion.p>
    </div>
  );
}

// ---------- 3. prompt ----------
const PROMPT_PARTS: [RegExp, string, string][] = [
  [
    /^(REHABILITATION OBJECTIVE|TARGET SKILL)/,
    "Objective",
    "bg-accent-soft border-accent",
  ],
  [
    /^(RECENT PERFORMANCE|RECENT WEAKNESS|PATIENT ANSWER|EXISTING ANALYSIS|RECORDED)/,
    "Context",
    "bg-[#f1eaf7] border-[#6b4a85]",
  ],
  [
    /^(EXERCISE TYPE|DIFFICULTY|ALLOWED|CANDIDATE|EXPECTED|OUTCOME)/,
    "Constraint",
    "bg-[#e5edf9] border-[#2f5ea8]",
  ],
  [/^TASK/, "Task", "bg-warning-soft border-warning"],
  [/^OUTPUT/, "Format", "bg-[#fde8ef] border-[#9d2c5a]"],
];

export function PromptVisual({ gen }: { gen: PipelineGeneration }) {
  const lines = (gen.user_prompt ?? "")
    .split("\n")
    .filter((l) => /^[A-Z][A-Z ]+[:(]/.test(l));
  return (
    <div className="flex flex-col gap-2">
      <motion.p
        {...rise(0)}
        className="rounded-xl bg-ink px-4 py-2 font-mono text-sm text-white"
      >
        SYSTEM · ROLE: RehabMind&rsquo;s assistant · not a diagnostician ·
        safety rules · JSON only
      </motion.p>
      {lines.map((l, i) => {
        const part = PROMPT_PARTS.find(([re]) => re.test(l));
        const [key, ...rest] = l.split(":");
        const value = rest.join(":").trim();
        return (
          <motion.div
            key={i}
            {...rise(i + 1)}
            className={cn(
              "flex gap-3 rounded-xl border-l-4 px-4 py-2",
              part?.[2] ?? "bg-canvas border-line-strong",
            )}
          >
            <span className="w-24 shrink-0 text-xs font-bold tracking-wide text-ink-muted uppercase">
              {part?.[1] ?? "Prompt"}
            </span>
            <span className="min-w-0 text-sm">
              <span className="font-bold">{key}:</span>{" "}
              {value.length > 110 ? `${value.slice(0, 110)}…` : value}
            </span>
          </motion.div>
        );
      })}
      <p className="text-sm text-ink-muted">
        Version <code className="font-mono">{gen.prompt_version}</code> + a JSON
        Schema the model must follow.
      </p>
    </div>
  );
}

// ---------- 4. transformer LLM ----------
export function LLMVisual({ gen }: { gen: PipelineGeneration }) {
  const a = gen.attempts.at(-1);
  const prompt = a?.usage?.prompt_tokens ?? 0;
  const output = a?.usage?.output_tokens ?? 0;
  const max = Math.max(prompt, output, 1);
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-accent px-3 py-1 font-bold text-white">
          {a?.model}
        </span>
        <span className="rounded-full bg-canvas px-3 py-1 text-sm ring-1 ring-line">
          decoder-only transformer · local GPU via Ollama
        </span>
        <span className="rounded-full bg-canvas px-3 py-1 text-sm ring-1 ring-line">
          {a?.latency_ms} ms
        </span>
      </div>
      {[
        ["Prompt tokens in", prompt, "bg-[#2f5ea8]"],
        ["Tokens generated", output, "bg-accent"],
      ].map(([label, n, color], i) => (
        <div key={String(label)} className="flex items-center gap-3">
          <span className="w-36 shrink-0 text-sm text-ink-muted">{label}</span>
          <div className="h-3 flex-1 overflow-hidden rounded-full bg-canvas">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(Number(n) / max) * 100}%` }}
              transition={{
                delay: 0.2 + i * 0.3,
                duration: 0.8,
                ease: "easeOut",
              }}
              className={cn("h-full rounded-full", String(color))}
            />
          </div>
          <span className="w-12 text-right font-bold tabular-nums">
            {String(n)}
          </span>
        </div>
      ))}
      <pre className="min-h-32 overflow-hidden rounded-2xl bg-ink p-4 text-sm leading-relaxed whitespace-pre-wrap text-[#bdf0e8]">
        <Typewriter
          text={a?.raw_output ?? "(no output: the model was unavailable)"}
        />
      </pre>
    </div>
  );
}

// ---------- 5. validation ----------
const STAGES = ["schema", "clinical", "safety"] as const;

export function ValidationVisual({ gen }: { gen: PipelineGeneration }) {
  const accepted = gen.attempts.some((a) => a.status === "accepted");
  return (
    <div className="flex flex-col gap-3">
      {gen.attempts.map((a, i) => {
        const failAt =
          a.status === "accepted"
            ? -1
            : STAGES.indexOf(a.failed_stage as (typeof STAGES)[number]);
        return (
          <motion.div
            key={i}
            {...rise(i)}
            className="rounded-2xl bg-canvas p-4"
          >
            <p className="mb-3 font-bold">Attempt {a.attempt}</p>
            {a.failed_stage === "provider" ? (
              <p className="text-sm">
                The model did not answer in time: counted as a failed attempt.
              </p>
            ) : (
              <div className="flex flex-wrap items-center gap-2">
                {STAGES.map((s, j) => {
                  const state =
                    failAt === -1 || j < failAt
                      ? "pass"
                      : j === failAt
                        ? "fail"
                        : "skip";
                  return (
                    <span key={s} className="flex items-center gap-2">
                      <motion.span
                        initial={{ scale: 0.6, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{
                          delay: 0.25 + i * 0.3 + j * 0.25,
                          type: "spring",
                          stiffness: 260,
                          damping: 16,
                        }}
                        className={cn(
                          "flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-bold capitalize",
                          state === "pass" && "bg-success-soft text-success",
                          state === "fail" && "bg-danger-soft text-danger",
                          state === "skip" &&
                            "bg-surface text-ink-muted ring-1 ring-line",
                        )}
                      >
                        {state === "pass" ? (
                          <Check aria-hidden="true" size={15} />
                        ) : state === "fail" ? (
                          <X aria-hidden="true" size={15} />
                        ) : null}
                        {s}
                      </motion.span>
                      {j < 2 && (
                        <ArrowRight
                          aria-hidden="true"
                          size={16}
                          className="text-ink-muted"
                        />
                      )}
                    </span>
                  );
                })}
              </div>
            )}
            {a.reason_codes.length > 0 && (
              <p className="mt-2 font-mono text-sm text-ink-muted">
                {a.reason_codes.join(", ")}
              </p>
            )}
          </motion.div>
        );
      })}
      <motion.p
        {...rise(gen.attempts.length + 1)}
        className={cn(
          "rounded-2xl px-4 py-3 text-lg font-bold",
          accepted
            ? "bg-success-soft text-success"
            : "bg-warning-soft text-warning",
        )}
      >
        {accepted
          ? "Accepted: the patient sees the AI's version."
          : "Not accepted: the patient gets a rule-based exercise instead."}
      </motion.p>
    </div>
  );
}

// ---------- 6. exercise ----------
export function ExerciseVisual({ t }: { t: Trace }) {
  return (
    <div className="flex flex-col items-center gap-4 text-center sm:flex-row sm:items-start sm:text-left">
      {t.image_url && (
        <motion.img
          initial={{ opacity: 0, scale: 0.94 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.45 }}
          src={t.image_url}
          alt={`Picture: ${t.picture ?? ""}`}
          width={240}
          height={180}
          className="h-48 w-auto rounded-2xl border-8 border-surface object-cover shadow-card ring-1 ring-line"
        />
      )}
      <div className="flex flex-col gap-3">
        <p className="text-2xl font-bold">{t.shown.prompt}</p>
        {t.shown.cues.length > 0 && (
          <div className="flex flex-col gap-1.5">
            {t.shown.cues.map((c, i) => (
              <motion.span
                key={c}
                {...rise(i + 1)}
                className="rounded-xl bg-accent-soft px-3 py-1.5 text-sm"
              >
                Hint {i + 1}: {c}
              </motion.span>
            ))}
          </div>
        )}
        {t.shown.words && (
          <div className="flex flex-wrap gap-1.5">
            {t.shown.words.map((w, i) => (
              <motion.span
                key={w + i}
                {...rise(i)}
                className="rounded-lg bg-accent px-3 py-1 font-bold text-white"
              >
                {w}
              </motion.span>
            ))}
          </div>
        )}
        <p className="text-sm text-ink-muted">
          {t.source === "ai" ? "Wording by the AI" : "Rule-based exercise"} ·
          picture, answers and word bank from the catalogue
        </p>
      </div>
    </div>
  );
}

// ---------- 7. response ----------
export function ResponseVisual({ t }: { t: Trace }) {
  const r = t.response;
  if (!r)
    return <p className="text-ink-muted">Waiting for the patient to answer.</p>;
  const Icon = r.mode === "speech" ? Mic : Keyboard;
  return (
    <div className="flex items-end gap-3">
      <span
        aria-hidden="true"
        className="grid size-12 shrink-0 place-items-center rounded-full bg-accent-soft font-bold text-accent-hover"
      >
        <Icon size={22} />
      </span>
      <motion.p
        initial={{ opacity: 0, x: -16, scale: 0.96 }}
        animate={{ opacity: 1, x: 0, scale: 1 }}
        transition={{ type: "spring", stiffness: 160, damping: 18 }}
        className="rounded-3xl rounded-bl-md bg-surface px-6 py-4 text-2xl shadow-card ring-1 ring-line"
      >
        {r.text ? `“${r.text}”` : "(the patient chose “I’m not sure”)"}
      </motion.p>
    </div>
  );
}

// ---------- 8. speech-to-text ----------
export function SpeechVisual({ t }: { t: Trace }) {
  const r = t.response;
  if (!r || r.mode !== "speech") {
    return (
      <div className="flex items-center gap-3 rounded-2xl bg-canvas p-4">
        <Keyboard aria-hidden="true" size={22} className="text-ink-muted" />
        <p>
          {r
            ? "Typed answer: speech recognition was not needed."
            : "No answer yet."}
        </p>
      </div>
    );
  }
  return (
    <div className="flex flex-wrap items-center gap-4">
      <div
        aria-hidden="true"
        className="flex h-16 items-center gap-1 rounded-2xl bg-[#e5edf9] px-4"
      >
        {Array.from({ length: 18 }, (_, i) => (
          <span
            key={i}
            className="w-1.5 animate-wave rounded-full bg-[#2f5ea8] motion-reduce:animate-none"
            style={{
              height: `${20 + ((i * 37) % 60)}%`,
              animationDelay: `${(i % 6) * 0.12}s`,
            }}
          />
        ))}
      </div>
      <ArrowRight aria-hidden="true" className="text-ink-muted" />
      <div className="rounded-2xl bg-surface px-5 py-3 shadow-card ring-1 ring-line">
        <p className="text-sm text-ink-muted">
          faster-whisper transcript (on this machine)
        </p>
        <p className="text-xl font-bold">
          <Typewriter text={`“${r.text ?? ""}”`} speed={30} />
        </p>
      </div>
    </div>
  );
}

// ---------- 9. NLP ----------
const MATCH: Record<string, string> = {
  exact: "Exact match",
  accepted_variant: "Accepted alternative word",
  plural: "Plural form",
  in_phrase: "Word found inside a short phrase",
  similar: "Close spelling or sound (edit distance)",
  word_order: "Right words, different order",
  none: "No match",
  skipped: "No answer given",
  concepts: "Key ideas checked",
};

export function NLPVisual({ t }: { t: Trace }) {
  const r = t.response;
  if (!r) return <p className="text-ink-muted">No answer to analyse yet.</p>;
  const tokens = (r.text ?? "").toLowerCase().split(/\s+/).filter(Boolean);
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-1.5">
        {tokens.length === 0 && (
          <span className="text-ink-muted">(no words)</span>
        )}
        {tokens.map((w, i) => (
          <motion.span
            key={i}
            {...rise(i)}
            className="rounded-lg bg-warning-soft px-3 py-1 font-mono text-warning"
          >
            {w}
          </motion.span>
        ))}
      </div>
      {r.concepts_matched ? (
        <div className="flex flex-wrap gap-2">
          {r.concepts_matched.map((c, i) => (
            <motion.span
              key={c}
              {...rise(i + 2)}
              className="flex items-center gap-1.5 rounded-full bg-success-soft px-3 py-1.5 font-bold text-success"
            >
              <Check aria-hidden="true" size={15} /> {c}
            </motion.span>
          ))}
          {(r.concepts_missing ?? []).map((c, i) => (
            <motion.span
              key={c}
              {...rise(i + 4)}
              className="flex items-center gap-1.5 rounded-full border-2 border-dashed border-warning px-3 py-1 font-bold text-warning"
            >
              <CircleX aria-hidden="true" size={15} /> {c}
            </motion.span>
          ))}
        </div>
      ) : (
        <p className="rounded-2xl bg-canvas px-4 py-3 text-lg">
          <span className="font-bold">
            {MATCH[r.match_type ?? "none"] ?? r.match_type}
          </span>
        </p>
      )}
    </div>
  );
}

// ---------- 10. score ----------
const OUTCOME_LABEL: Record<string, string> = {
  correct: "Correct",
  near_miss: "Close",
  incorrect: "Not correct",
  skipped: "Skipped",
};

export function ScoreVisual({ t }: { t: Trace }) {
  const r = t.response;
  if (!r) return <p className="text-ink-muted">Not scored yet.</p>;
  const len = 2 * Math.PI * 52;
  return (
    <div className="flex flex-wrap items-center gap-6">
      <div
        aria-hidden="true"
        className="relative grid size-36 place-items-center"
      >
        <svg viewBox="0 0 120 120" className="absolute inset-0 -rotate-90">
          <circle
            cx="60"
            cy="60"
            r="52"
            fill="none"
            strokeWidth="12"
            className="stroke-accent-soft"
          />
          <motion.circle
            cx="60"
            cy="60"
            r="52"
            fill="none"
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={len}
            initial={{ strokeDashoffset: len }}
            animate={{ strokeDashoffset: len * (1 - r.score) }}
            transition={{ duration: 1, ease: "easeOut" }}
            className="stroke-accent"
          />
        </svg>
        <span className="text-3xl font-bold tabular-nums">{r.score}</span>
      </div>
      <div className="flex flex-col gap-1">
        <p className="text-3xl font-bold">
          {OUTCOME_LABEL[r.outcome] ?? r.outcome}
        </p>
        <p className="text-ink-muted">
          Fixed rules decide this. The AI can never change it.
        </p>
      </div>
    </div>
  );
}

// ---------- 11. feedback ----------
export function FeedbackVisual({ gen }: { gen: PipelineGeneration | null }) {
  if (!gen)
    return (
      <p className="text-ink-muted">
        No AI feedback was requested for this answer.
      </p>
    );
  if (!gen.output) {
    return (
      <p className="rounded-2xl bg-warning-soft px-4 py-3">
        The model&rsquo;s tips were rejected (
        {gen.attempts.flatMap((a) => a.reason_codes).join(", ")}), so the
        patient kept the standard feedback.
      </p>
    );
  }
  return (
    <div className="flex gap-4 rounded-3xl border border-accent/20 bg-accent-soft px-6 py-5">
      <span
        aria-hidden="true"
        className="grid size-12 shrink-0 place-items-center rounded-full bg-surface text-warning shadow-sm"
      >
        <Lightbulb size={24} />
      </span>
      <div className="flex flex-col gap-1">
        <p className="text-sm font-bold text-accent-hover">A tip for you</p>
        <p className="text-2xl">
          <Typewriter text={String(gen.output.feedback)} speed={22} />
        </p>
        {gen.output.optional_hint ? (
          <p className="text-lg text-ink-muted">
            {String(gen.output.optional_hint)}
          </p>
        ) : null}
      </div>
    </div>
  );
}

// ---------- 12. next ----------
export function NextVisual({ next }: { next: Trace | undefined }) {
  if (!next)
    return (
      <p className="text-ink-muted">
        The next exercise has not been issued yet.
      </p>
    );
  return (
    <div className="flex flex-wrap items-center gap-5">
      <motion.span
        aria-hidden="true"
        animate={{ rotate: 360 }}
        transition={{ duration: 2.4, ease: "easeInOut" }}
        className="grid size-16 place-items-center rounded-full bg-accent-soft text-accent"
      >
        <Repeat size={30} />
      </motion.span>
      {next.image_url && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={next.image_url}
          alt={`Next picture: ${next.picture ?? ""}`}
          width={160}
          height={120}
          className="h-28 w-auto rounded-2xl border-4 border-surface object-cover shadow-card"
        />
      )}
      <div>
        <p className="text-xl font-bold">
          Picture {next.position}: {next.objective_label}
        </p>
        <p className="text-ink-muted">
          Difficulty {next.difficulty} ·{" "}
          {next.source === "ai" ? "AI-generated" : "rule-based"} · the loop
          starts again
        </p>
      </div>
    </div>
  );
}
