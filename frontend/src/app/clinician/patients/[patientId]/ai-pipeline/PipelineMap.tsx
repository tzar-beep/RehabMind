"use client";

import {
  AudioLines,
  BrainCircuit,
  Braces,
  CheckCircle2,
  ClipboardCheck,
  Cpu,
  Gauge,
  Image as ImageIcon,
  Lightbulb,
  MessageSquareText,
  Pause,
  Play,
  Repeat,
  ScanText,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import type { Pipeline, PipelineGeneration } from "@/lib/api/clinician";
import { cn } from "@/lib/utils";

type Trace = Pipeline["traces"][number];
type State = "ok" | "warn" | "fail" | "skip" | "idle";
type Concept = "ML" | "DL" | "NLP" | "Transformer" | "GenAI" | "Rules";

interface Node {
  id: string;
  lane: 0 | 1 | 2;
  title: string;
  concept: Concept;
  icon: LucideIcon;
  summary: string;
  state: State;
  explain: string;
  detail: ReactNode;
}

const LANES = [
  {
    title: "1 · Generate",
    text: "Learn from performance and write the next exercise",
  },
  { title: "2 · Practise", text: "The patient answers; the app scores it" },
  { title: "3 · Respond", text: "Supportive feedback, then the loop repeats" },
];

const CONCEPT_STYLE: Record<Concept, string> = {
  ML: "bg-[#f1eaf7] text-[#6b4a85]",
  DL: "bg-[#e5edf9] text-[#2f5ea8]",
  NLP: "bg-warning-soft text-warning",
  Transformer: "bg-accent-soft text-accent-hover",
  GenAI: "bg-[#fde8ef] text-[#9d2c5a]",
  Rules: "bg-canvas text-ink-muted ring-1 ring-line",
};

const STATE_STYLE: Record<
  State,
  { ring: string; dot: string; beam: string; label: string }
> = {
  ok: {
    ring: "border-success/40",
    dot: "bg-success",
    beam: "#2e8b57",
    label: "passed",
  },
  warn: {
    ring: "border-warning/50",
    dot: "bg-[#c27c2c]",
    beam: "#c27c2c",
    label: "retried or fell back",
  },
  fail: {
    ring: "border-danger/40",
    dot: "bg-danger",
    beam: "#a12a2a",
    label: "failed safely",
  },
  skip: {
    ring: "border-line",
    dot: "bg-line-strong",
    beam: "#b9b2a6",
    label: "not needed",
  },
  idle: {
    ring: "border-dashed border-line-strong",
    dot: "bg-line",
    beam: "#cfc8bd",
    label: "not reached yet",
  },
};

const OBJECTIVE_SHORT: Record<string, string> = {
  word_retrieval: "Word retrieval",
  sentence_formation: "Sentences",
  descriptive_language: "Description",
};

const time = (iso: string) =>
  new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));

const OUTCOME: Record<string, string> = {
  correct: "Correct",
  near_miss: "Close",
  incorrect: "Not correct",
  skipped: "Skipped",
};

function Code({ value }: { value: unknown }) {
  return (
    <pre
      tabIndex={0}
      aria-label="Data"
      className="max-h-80 overflow-auto rounded-control bg-ink p-4 text-sm leading-relaxed whitespace-pre-wrap text-white"
    >
      {typeof value === "string" ? value : JSON.stringify(value, null, 2)}
    </pre>
  );
}

function Attempts({ gen }: { gen: PipelineGeneration }) {
  return (
    <ul className="flex flex-col gap-2">
      {gen.attempts.map((a, i) => (
        <li key={i} className="rounded-control border border-line p-3 text-sm">
          <span
            className={cn(
              "mr-2 rounded-full px-2 py-0.5 font-bold",
              a.status === "accepted"
                ? "bg-success-soft text-success"
                : "bg-warning-soft text-warning",
            )}
          >
            Attempt {a.attempt}:{" "}
            {a.status === "accepted"
              ? "valid"
              : `${a.status} at ${a.failed_stage}`}
          </span>
          <span className="text-ink-muted">
            {a.model} · {a.latency_ms} ms
            {a.usage?.output_tokens
              ? ` · ${a.usage.prompt_tokens} → ${a.usage.output_tokens} tokens`
              : ""}
          </span>
          {a.reason_codes.length > 0 && (
            <span className="mt-1 block font-mono text-ink-muted">
              {a.reason_codes.join(", ")}
            </span>
          )}
        </li>
      ))}
    </ul>
  );
}

function generationState(gen: PipelineGeneration | null): State {
  if (!gen) return "skip";
  const accepted = gen.attempts.find((a) => a.status === "accepted");
  if (accepted)
    return accepted.attempt === 1 && gen.attempts.length === 1 ? "ok" : "warn";
  return "fail";
}

function buildNodes(
  t: Trace,
  next: Trace | undefined,
  abilities: Pipeline["abilities"],
): Node[] {
  const gen = t.generation;
  const ctx = (gen?.context ?? {}) as Record<string, unknown>;
  const first = gen?.attempts[0];
  const llmOk = gen?.attempts.some((a) => a.status !== "error");
  const ab = abilities[t.objective];
  const r = t.response;
  const acc =
    typeof ctx.recent_accuracy === "number"
      ? Math.round(ctx.recent_accuracy * 100)
      : ab?.recent_accuracy != null
        ? Math.round(ab.recent_accuracy * 100)
        : null;
  const fb = t.feedback;
  const fbState: State = !fb
    ? r
      ? "skip"
      : "idle"
    : fb.output
      ? generationState(fb)
      : "warn";

  return [
    {
      id: "performance",
      lane: 0,
      title: "Patient performance",
      concept: "ML",
      icon: BrainCircuit,
      summary: `θ ${Number(ctx.ability ?? ab?.ability ?? 0).toFixed(2)} · ${acc ?? "—"}% · ${String(ctx.trend ?? ab?.trend ?? "").replaceAll("_", " ")}`,
      state: gen ? "ok" : "skip",
      explain:
        "Machine learning: an online logistic (Rasch/Elo-style) model learns the patient's ability for this objective from every scored answer since the latest fresh start.",
      detail: (
        <Code
          value={{
            ability: ctx.ability,
            recent_accuracy: ctx.recent_accuracy,
            trend: ctx.trend,
            status: ctx.status,
            predicted_success: ctx.predicted_success,
            recent_outcomes: ctx.recent_outcomes,
          }}
        />
      ),
    },
    {
      id: "context",
      lane: 0,
      title: "Structured context",
      concept: "Rules",
      icon: Braces,
      summary: gen
        ? `Difficulty ${String(ctx.target_difficulty)} of ${String(ctx.min_difficulty)}–${String(ctx.max_difficulty)} · ${Array.isArray(ctx.candidates) ? ctx.candidates.length : 0} pictures`
        : "AI not used",
      state: gen ? "ok" : "skip",
      explain:
        "The application fixes the objective, exercise type, difficulty (rule-based, inside the clinician's limits) and the approved pictures. No names, emails or IDs.",
      detail: gen ? (
        <Code value={ctx} />
      ) : (
        <p className="text-ink-muted">No AI request for this exercise.</p>
      ),
    },
    {
      id: "prompt",
      lane: 0,
      title: "Prompt engineering",
      concept: "GenAI",
      icon: ScanText,
      summary: gen
        ? `${gen.prompt_version} · ${first?.usage?.prompt_tokens ?? "—"} tokens`
        : "—",
      state: gen ? "ok" : "skip",
      explain:
        "A versioned prompt: role, objective, patient context, constraints, task, safety rules and a JSON Schema for the answer.",
      detail: gen ? (
        <div className="flex flex-col gap-3">
          <p className="text-sm font-bold text-ink-muted">System message</p>
          <Code value={gen.system_prompt ?? "(older prompt version)"} />
          <p className="text-sm font-bold text-ink-muted">User message</p>
          <Code value={gen.user_prompt ?? "(older prompt version)"} />
        </div>
      ) : (
        <p className="text-ink-muted">No prompt for this exercise.</p>
      ),
    },
    {
      id: "llm",
      lane: 0,
      title: "Transformer LLM",
      concept: "Transformer",
      icon: Cpu,
      summary: first ? `${first.model} · ${first.latency_ms} ms` : "—",
      state: !gen ? "skip" : llmOk ? "ok" : "fail",
      explain:
        "A decoder-only transformer running locally through Ollama generates the content, constrained to the JSON Schema.",
      detail: gen ? (
        <div className="flex flex-col gap-3">
          <Attempts gen={gen} />
          {gen.attempts.at(-1)?.raw_output && (
            <Code value={gen.attempts.at(-1)!.raw_output} />
          )}
        </div>
      ) : (
        <p className="text-ink-muted">
          The model was not called for this exercise.
        </p>
      ),
    },
    {
      id: "validation",
      lane: 0,
      title: "Validation",
      concept: "Rules",
      icon: ShieldCheck,
      summary: !gen
        ? "—"
        : gen.output
          ? gen.attempts.length === 1
            ? "Valid first time"
            : `Valid after ${gen.attempts.length} attempts`
          : "Rejected → rule-based exercise",
      state: generationState(gen),
      explain:
        "Schema → clinical → safety checks (approved picture, difficulty in range, no answer leak, no medical claims). Failures retry once, then fall back to rules.",
      detail: gen ? (
        <Attempts gen={gen} />
      ) : (
        <p className="text-ink-muted">Nothing to validate.</p>
      ),
    },
    {
      id: "exercise",
      lane: 1,
      title: "Exercise shown",
      concept: "Rules",
      icon: ImageIcon,
      summary: `${t.shown.prompt ?? ""}`,
      state: "ok",
      explain:
        "The ExerciseIssuer re-checks every rule and a database trigger refuses anything out of range. Pictures and answers always come from the catalogue.",
      detail: (
        <div className="flex flex-wrap gap-4">
          {t.image_url && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={t.image_url}
              alt={`Picture: ${t.picture ?? ""}`}
              width={160}
              height={120}
              className="h-32 w-auto rounded-control border border-line object-cover"
            />
          )}
          <div className="flex flex-col gap-1">
            <p className="text-lg font-bold">{t.shown.prompt}</p>
            <p className="text-ink-muted">
              {t.objective_label} · {t.exercise_type.replaceAll("_", " ")} ·
              difficulty {t.difficulty}
            </p>
            {t.shown.cues.length > 0 && (
              <p>Hints: {t.shown.cues.join(" · ")}</p>
            )}
            {t.shown.words && <p>Word bank: {t.shown.words.join(", ")}</p>}
            <p className="text-sm text-ink-muted">
              Source:{" "}
              {t.source === "ai"
                ? "AI-generated"
                : t.source === "rule"
                  ? "rule-based"
                  : "fallback"}
            </p>
          </div>
        </div>
      ),
    },
    {
      id: "response",
      lane: 1,
      title: "Patient response",
      concept: "Rules",
      icon: MessageSquareText,
      summary: r ? `“${r.text ?? "skipped"}” · ${r.mode}` : "Not answered yet",
      state: r ? "ok" : "idle",
      explain: "The patient types, taps word tiles or speaks.",
      detail: r ? (
        <Code
          value={{ text: r.text, mode: r.mode, hints_used: r.hints_used }}
        />
      ) : (
        <p className="text-ink-muted">Waiting for an answer.</p>
      ),
    },
    {
      id: "stt",
      lane: 1,
      title: "Speech-to-text",
      concept: "DL",
      icon: AudioLines,
      summary: !r
        ? "—"
        : r.mode === "speech"
          ? "faster-whisper transcript"
          : "Typed: not needed",
      state: !r ? "idle" : r.mode === "speech" ? "ok" : "skip",
      explain:
        "Deep learning: faster-whisper (an encoder–decoder transformer) transcribes speech on this machine; unreliable transcripts are never scored and audio is deleted.",
      detail:
        r?.mode === "speech" ? (
          <Code value={{ transcript: r.text }} />
        ) : (
          <p className="text-ink-muted">
            This answer was typed, so no speech recognition was needed.
          </p>
        ),
    },
    {
      id: "nlp",
      lane: 1,
      title: "NLP analysis",
      concept: "NLP",
      icon: Lightbulb,
      summary: !r
        ? "—"
        : r.concepts_matched
          ? `${r.concepts_matched.length} key ideas found`
          : `match: ${(r.match_type ?? "none").replaceAll("_", " ")}`,
      state: r ? "ok" : "idle",
      explain:
        "Normalisation, edit-distance matching, concept coverage and word-order analysis turn the answer into structured findings.",
      detail: r ? (
        <Code
          value={{
            match_type: r.match_type,
            concepts_matched: r.concepts_matched,
            concepts_missing: r.concepts_missing,
          }}
        />
      ) : (
        <p className="text-ink-muted">No answer to analyse yet.</p>
      ),
    },
    {
      id: "score",
      lane: 1,
      title: "Deterministic score",
      concept: "Rules",
      icon: ClipboardCheck,
      summary: r ? `${OUTCOME[r.outcome] ?? r.outcome} · ${r.score}` : "—",
      state: r ? "ok" : "idle",
      explain:
        "The official score comes from fixed rules. The AI can never change it.",
      detail: r ? (
        <Code value={{ outcome: r.outcome, score: r.score }} />
      ) : (
        <p className="text-ink-muted">Not scored yet.</p>
      ),
    },
    {
      id: "feedback",
      lane: 2,
      title: "AI feedback",
      concept: "GenAI",
      icon: Lightbulb,
      summary: fb?.output
        ? String(fb.output.feedback)
        : fb
          ? "Standard feedback kept"
          : r
            ? "Not requested"
            : "—",
      state: fbState,
      explain:
        "After scoring, the LLM writes a short supportive tip (feedback_generation_v1). Tips that contradict the score are rejected.",
      detail: fb ? (
        <div className="flex flex-col gap-3">
          {fb.output && (
            <p className="rounded-control bg-accent-soft p-4 text-lg">
              {String(fb.output.feedback)}{" "}
              {fb.output.optional_hint ? String(fb.output.optional_hint) : ""}
            </p>
          )}
          <Attempts gen={fb} />
        </div>
      ) : (
        <p className="text-ink-muted">No AI feedback for this answer.</p>
      ),
    },
    {
      id: "next",
      lane: 2,
      title: "Next exercise",
      concept: "Rules",
      icon: Repeat,
      summary: next
        ? `Picture ${next.position} · difficulty ${next.difficulty}`
        : "Not issued yet",
      state: next ? "ok" : "idle",
      explain: "The updated performance feeds the next turn of the loop.",
      detail: next ? (
        <p>
          Picture {next.position}: {next.objective_label}, difficulty{" "}
          {next.difficulty} (
          {next.source === "ai" ? "AI-generated" : "rule-based"}).
        </p>
      ) : (
        <p className="text-ink-muted">
          The next exercise has not been issued yet.
        </p>
      ),
    },
  ];
}

type Beam = { d: string; color: string; state: State; key: string };

export function PipelineMap({ data }: { data: Pipeline }) {
  const [traceIndex, setTraceIndex] = useState(() =>
    Math.max(
      0,
      data.traces.findIndex((t) => t.response !== null),
    ),
  );
  const [selected, setSelected] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [beams, setBeams] = useState<Beam[]>([]);
  const container = useRef<HTMLDivElement>(null);
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const selectedChip = useRef<HTMLButtonElement | null>(null);

  // Keep the chosen exercise visible in the scrolling row of buttons.
  useEffect(() => {
    // Horizontal only: never scroll the page itself.
    const chip = selectedChip.current;
    const row = chip?.parentElement;
    if (chip && row)
      row.scrollLeft = Math.max(0, chip.offsetLeft - row.offsetLeft - 16);
  }, [traceIndex]);

  const trace = data.traces[traceIndex];
  const nodes = trace
    ? buildNodes(trace, data.traces[traceIndex - 1], data.abilities)
    : [];

  const layout = useCallback(() => {
    const box = container.current?.getBoundingClientRect();
    if (!box) return;
    const out: Beam[] = [];
    for (let i = 0; i < nodes.length - 1; i++) {
      const a = refs.current[i]?.getBoundingClientRect();
      const b = refs.current[i + 1]?.getBoundingClientRect();
      if (!a || !b) continue;
      const sameRow = Math.abs(a.top - b.top) < 20;
      let d: string;
      if (sameRow) {
        const x1 = a.right - box.left,
          y1 = a.top + a.height / 2 - box.top;
        const x2 = b.left - box.left,
          y2 = b.top + b.height / 2 - box.top;
        d = `M${x1},${y1} C${x1 + 12},${y1} ${x2 - 12},${y2} ${x2},${y2}`;
      } else {
        const x1 = a.left + a.width / 2 - box.left,
          y1 = a.bottom - box.top;
        const x2 = b.left + b.width / 2 - box.left,
          y2 = b.top - box.top;
        const mid = (y1 + y2) / 2;
        d = `M${x1},${y1} C${x1},${mid} ${x2},${mid} ${x2},${y2}`;
      }
      const state = nodes[i + 1].state;
      out.push({ d, color: STATE_STYLE[state].beam, state, key: `${i}` });
    }
    setBeams(out);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [traceIndex, nodes.length]);

  useLayoutEffect(() => {
    layout();
    const ro = new ResizeObserver(layout);
    if (container.current) ro.observe(container.current);
    return () => ro.disconnect();
  }, [layout]);

  useEffect(() => {
    if (!playing) return;
    const t = setTimeout(() => {
      if (selected >= nodes.length - 1) setPlaying(false);
      else setSelected(selected + 1);
    }, 1200);
    return () => clearTimeout(t);
  }, [playing, selected, nodes.length]);

  if (!trace) {
    return (
      <p className="text-ink-muted">
        No exercises yet. Start a practice session as the patient.
      </p>
    );
  }
  const node = nodes[selected];
  const lanes = [0, 1, 2] as const;
  let index = -1;

  return (
    <div className="flex flex-col gap-6">
      {/* Which exercise to follow */}
      <div className="flex flex-col gap-2">
        <p id="trace-picker" className="text-sm font-bold text-ink-muted">
          Follow an exercise through the pipeline
        </p>
        <div
          role="group"
          aria-labelledby="trace-picker"
          className="flex gap-2 overflow-x-auto pb-1"
        >
          {data.traces.map((t, i) => (
            <button
              key={`${t.issued_at}-${t.position}`}
              type="button"
              aria-pressed={i === traceIndex}
              ref={(el) => {
                if (i === traceIndex) selectedChip.current = el;
              }}
              onClick={() => {
                setTraceIndex(i);
                setSelected(0);
                setPlaying(false);
              }}
              className={cn(
                "flex min-h-target shrink-0 items-center gap-2 rounded-full border-2 px-4 text-sm font-bold transition-colors",
                i === traceIndex
                  ? "border-accent bg-accent text-white"
                  : "border-line bg-surface text-ink hover:border-accent/50",
              )}
            >
              <span
                aria-hidden="true"
                className={cn(
                  "size-2.5 rounded-full",
                  i === traceIndex
                    ? "bg-white"
                    : STATE_STYLE[generationState(t.generation)].dot,
                )}
              />
              Picture {t.position} ·{" "}
              {OBJECTIVE_SHORT[t.objective] ?? t.objective}
              <span className="font-normal">{time(t.issued_at)}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Controls + legend */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => {
              if (!playing && selected >= nodes.length - 1) setSelected(0);
              setPlaying((p) => !p);
            }}
            className="inline-flex min-h-target items-center gap-2 rounded-control bg-accent px-5 font-bold text-white hover:bg-accent-hover"
          >
            {playing ? (
              <Pause aria-hidden="true" size={18} />
            ) : (
              <Play aria-hidden="true" size={18} />
            )}
            {playing ? "Pause" : "Play the pipeline"}
          </button>
        </div>
        <ul
          aria-label="Concepts"
          className="flex flex-wrap gap-1.5 text-xs font-bold"
        >
          {(Object.keys(CONCEPT_STYLE) as Concept[]).map((c) => (
            <li
              key={c}
              className={cn("rounded-full px-2.5 py-1", CONCEPT_STYLE[c])}
            >
              {c}
            </li>
          ))}
        </ul>
      </div>

      <Stats traces={data.traces} />

      {/* The map */}
      <div
        ref={container}
        className="relative isolate rounded-card border border-line bg-[radial-gradient(var(--color-line)_1px,transparent_1px)] bg-size-[18px_18px] p-4 sm:p-6"
      >
        <svg
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 -z-10 size-full overflow-visible"
        >
          {beams.map((b, i) => {
            const active = i === selected - 1;
            const live = b.state === "ok" || b.state === "warn";
            return (
              <g key={b.key}>
                <path
                  d={b.d}
                  fill="none"
                  stroke={b.color}
                  strokeOpacity={live ? 0.35 : 0.5}
                  strokeWidth={active ? 5 : 3}
                  strokeDasharray={live ? undefined : "4 6"}
                  strokeLinecap="round"
                />
                {live && (
                  <path
                    d={b.d}
                    fill="none"
                    stroke={b.color}
                    strokeWidth={active ? 5 : 3}
                    strokeLinecap="round"
                    className="animate-flow motion-reduce:animate-none"
                    strokeDasharray="10 22"
                  />
                )}
              </g>
            );
          })}
        </svg>

        <div className="flex flex-col gap-8">
          {lanes.map((lane) => (
            <section
              key={lane}
              aria-label={LANES[lane].title}
              className="flex flex-col gap-3"
            >
              <div className="flex w-fit flex-wrap items-baseline gap-x-3 rounded-control bg-canvas px-2 py-1">
                <h3 className="text-sm font-bold tracking-wide text-accent-hover uppercase">
                  {LANES[lane].title}
                </h3>
                <p className="text-sm text-ink-muted">{LANES[lane].text}</p>
              </div>
              <ol className="grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
                {nodes
                  .filter((n) => n.lane === lane)
                  .map((n) => {
                    index += 1;
                    const i = index;
                    const Icon = n.icon;
                    const isSel = i === selected;
                    return (
                      <li key={n.id}>
                        <button
                          ref={(el) => {
                            refs.current[i] = el;
                          }}
                          type="button"
                          aria-pressed={isSel}
                          onClick={() => {
                            setSelected(i);
                            setPlaying(false);
                          }}
                          className={cn(
                            "flex h-full w-full flex-col gap-1.5 rounded-card border-2 bg-surface p-3 text-left shadow-card transition-all",
                            STATE_STYLE[n.state].ring,
                            isSel &&
                              "-translate-y-0.5 border-accent ring-4 ring-accent/20",
                            n.state === "skip" || n.state === "idle"
                              ? "bg-canvas shadow-none"
                              : "",
                          )}
                        >
                          <span className="flex items-center justify-between gap-2">
                            <span
                              aria-hidden="true"
                              className={cn(
                                "grid size-8 place-items-center rounded-lg",
                                CONCEPT_STYLE[n.concept],
                              )}
                            >
                              <Icon size={17} />
                            </span>
                            <span
                              className={cn(
                                "rounded-full px-2 py-0.5 text-xs font-bold",
                                CONCEPT_STYLE[n.concept],
                              )}
                            >
                              {n.concept}
                            </span>
                          </span>
                          <span className="flex items-center gap-2 font-bold">
                            <span
                              aria-hidden="true"
                              className={cn(
                                "size-2.5 shrink-0 rounded-full",
                                STATE_STYLE[n.state].dot,
                              )}
                            />
                            {i + 1}. {n.title}
                          </span>
                          <span className="line-clamp-1 text-sm text-ink-muted">
                            {n.summary}
                          </span>
                          <span className="sr-only">
                            Status: {STATE_STYLE[n.state].label}
                          </span>
                        </button>
                      </li>
                    );
                  })}
              </ol>
            </section>
          ))}
        </div>
      </div>

      {/* Details of the selected step */}
      <section
        aria-live="polite"
        aria-labelledby="step-title"
        className="flex flex-col gap-4 rounded-card border border-line bg-surface p-6 shadow-card"
      >
        <div className="flex flex-wrap items-center gap-3">
          <span
            className={cn(
              "rounded-full px-3 py-1 text-sm font-bold",
              CONCEPT_STYLE[node.concept],
            )}
          >
            {node.concept}
          </span>
          <h3 id="step-title" className="text-xl font-bold">
            Step {selected + 1}: {node.title}
          </h3>
          <span className="flex items-center gap-1.5 text-sm text-ink-muted">
            {node.state === "ok" ? (
              <CheckCircle2
                aria-hidden="true"
                size={16}
                className="text-success"
              />
            ) : (
              <Gauge aria-hidden="true" size={16} />
            )}
            {STATE_STYLE[node.state].label}
          </span>
        </div>
        <p className="text-ink-muted">{node.explain}</p>
        {node.detail}
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={selected === 0}
            onClick={() => setSelected((s) => Math.max(0, s - 1))}
            className="min-h-target rounded-control border-2 border-line-strong px-4 font-bold disabled:opacity-50"
          >
            ← Previous step
          </button>
          <button
            type="button"
            disabled={selected === nodes.length - 1}
            onClick={() =>
              setSelected((s) => Math.min(nodes.length - 1, s + 1))
            }
            className="min-h-target rounded-control border-2 border-accent px-4 font-bold text-accent disabled:opacity-50"
          >
            Next step →
          </button>
        </div>
      </section>
    </div>
  );
}

/** Headline numbers across the listed exercises (all computed from the audit log). */
function Stats({ traces }: { traces: Trace[] }) {
  const gens = traces
    .map((t) => t.generation)
    .filter((g): g is PipelineGeneration => !!g);
  const attempts = gens.flatMap((g) => g.attempts);
  const firstTry = gens.filter(
    (g) => g.attempts[0]?.status === "accepted",
  ).length;
  const answered = attempts.filter((a) => a.status !== "error");
  const latency = answered.length
    ? answered.reduce((sum, a) => sum + a.latency_ms, 0) /
      answered.length /
      1000
    : null;
  const tips = traces.filter((t) => t.feedback?.output).length;
  const items = [
    {
      label: "AI-generated exercises",
      value: `${traces.filter((t) => t.source === "ai").length} of ${traces.length}`,
    },
    {
      label: "Valid on the first try",
      value: gens.length
        ? `${Math.round((100 * firstTry) / gens.length)}%`
        : "—",
    },
    {
      label: "Average model time",
      value: latency === null ? "—" : `${latency.toFixed(1)} s`,
    },
    { label: "Feedback tips written", value: String(tips) },
  ];
  return (
    <dl className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {items.map((it) => (
        <div
          key={it.label}
          className="flex flex-col-reverse rounded-card border border-line bg-linear-to-br from-surface to-accent-soft/60 p-4"
        >
          <dt className="text-sm text-ink-muted">{it.label}</dt>
          <dd className="text-2xl font-bold tabular-nums">{it.value}</dd>
        </div>
      ))}
    </dl>
  );
}
