"use client";

import {
  AudioLines,
  BrainCircuit,
  Braces,
  ChevronLeft,
  ChevronRight,
  ClipboardCheck,
  Cpu,
  Image as ImageIcon,
  Lightbulb,
  MessageSquareText,
  Pause,
  Play,
  Repeat,
  ScanText,
  ShieldCheck,
  Sparkles,
  Timer,
  Wand2,
  type LucideIcon,
} from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
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

import {
  AbilityVisual,
  ContextVisual,
  ExerciseVisual,
  FeedbackVisual,
  LLMVisual,
  NLPVisual,
  NextVisual,
  PromptVisual,
  ResponseVisual,
  ScoreVisual,
  SpeechVisual,
  ValidationVisual,
} from "./slides";

type Trace = Pipeline["traces"][number];
type State = "ok" | "warn" | "fail" | "skip" | "idle";
type Concept = "ML" | "DL" | "NLP" | "Transformer" | "GenAI" | "Rules";

interface Step {
  id: string;
  lane: 0 | 1 | 2;
  title: string;
  concept: Concept;
  icon: LucideIcon;
  summary: string;
  state: State;
  explain: string;
  visual: ReactNode;
  raw: unknown;
  /** How long the slide stays up while playing. */
  ms: number;
}

const LANES = [
  {
    title: "Generate",
    text: "Learn from performance, write the next exercise",
  },
  { title: "Practise", text: "The patient answers; fixed rules score it" },
  { title: "Respond", text: "Supportive feedback, then the loop repeats" },
];

const CONCEPT_LIGHT: Record<Concept, string> = {
  ML: "bg-[#f1eaf7] text-[#6b4a85]",
  DL: "bg-[#e5edf9] text-[#2f5ea8]",
  NLP: "bg-warning-soft text-warning",
  Transformer: "bg-accent-soft text-accent-hover",
  GenAI: "bg-[#fde8ef] text-[#9d2c5a]",
  Rules: "bg-canvas text-ink-muted ring-1 ring-line",
};

const STATE: Record<State, { dot: string; beam: string; label: string }> = {
  ok: { dot: "bg-[#6ee7b7]", beam: "#5eead4", label: "passed" },
  warn: { dot: "bg-[#fbbf24]", beam: "#fbbf24", label: "retried or fell back" },
  fail: { dot: "bg-[#f87171]", beam: "#f87171", label: "failed safely" },
  skip: { dot: "bg-[#94a3b8]", beam: "#94a3b8", label: "not needed" },
  idle: { dot: "bg-[#64748b]", beam: "#64748b", label: "not reached yet" },
};

// Status dots on the light cards (the map's beams keep the brighter colours).
const DOT_ON_LIGHT: Record<State, string> = {
  ok: "bg-success",
  warn: "bg-[#c27c2c]",
  fail: "bg-danger",
  skip: "bg-line-strong",
  idle: "bg-line",
};

function genState(gen: PipelineGeneration | null): State {
  if (!gen) return "skip";
  const ok = gen.attempts.find((a) => a.status === "accepted");
  if (ok) return ok.attempt === 1 && gen.attempts.length === 1 ? "ok" : "warn";
  return "fail";
}

const pct = (v: unknown) =>
  typeof v === "number" ? `${Math.round(v * 100)}%` : "—";

function buildSteps(t: Trace, next: Trace | undefined): Step[] {
  const gen = t.generation;
  const ctx = (gen?.context ?? {}) as Record<string, unknown>;
  const last = gen?.attempts.at(-1);
  const r = t.response;
  const fb = t.feedback;
  const noAi = (
    <p className="text-lg text-ink-muted">
      No AI request was made for this exercise.
    </p>
  );
  return [
    {
      id: "performance",
      lane: 0,
      title: "Patient performance",
      concept: "ML",
      icon: BrainCircuit,
      summary: gen
        ? `θ ${Number(ctx.ability ?? 0).toFixed(2)} · ${pct(ctx.recent_accuracy)} · ${String(ctx.trend ?? "").replaceAll("_", " ")}`
        : "—",
      state: gen ? "ok" : "skip",
      explain:
        "Machine learning: an online logistic (Rasch / Elo-style) model learns the patient's ability for this objective from every scored answer.",
      visual: gen ? <AbilityVisual ctx={ctx} /> : noAi,
      raw: gen ? ctx : null,
      ms: 5000,
    },
    {
      id: "context",
      lane: 0,
      title: "Structured context",
      concept: "Rules",
      icon: Braces,
      summary: gen
        ? `Level ${String(ctx.target_difficulty)} · ${Array.isArray(ctx.candidates) ? ctx.candidates.length : 0} pictures`
        : "AI not used",
      state: gen ? "ok" : "skip",
      explain:
        "The application fixes the objective, exercise type, difficulty (inside the clinician's limits) and the approved pictures. No names, emails or IDs.",
      visual: gen ? <ContextVisual ctx={ctx} /> : noAi,
      raw: ctx,
      ms: 5000,
    },
    {
      id: "prompt",
      lane: 0,
      title: "Prompt engineering",
      concept: "GenAI",
      icon: ScanText,
      summary: gen ? gen.prompt_version : "—",
      state: gen ? "ok" : "skip",
      explain:
        "A versioned, structured prompt: role, objective, patient context, constraints, task, safety rules and a JSON output format.",
      visual: gen ? <PromptVisual gen={gen} /> : noAi,
      raw: gen ? { system: gen.system_prompt, user: gen.user_prompt } : null,
      ms: 6500,
    },
    {
      id: "llm",
      lane: 0,
      title: "Transformer LLM",
      concept: "Transformer",
      icon: Cpu,
      summary: last
        ? `${last.model} · ${(last.latency_ms / 1000).toFixed(1)} s`
        : "—",
      state: !gen
        ? "skip"
        : gen.attempts.some((a) => a.status !== "error")
          ? "ok"
          : "fail",
      explain:
        "A decoder-only transformer running locally through Ollama writes the content, constrained to the JSON Schema.",
      visual: gen ? <LLMVisual gen={gen} /> : noAi,
      raw: gen?.attempts ?? null,
      ms: 7000,
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
            : `Valid after ${gen.attempts.length} tries`
          : "Rejected → rules",
      state: genState(gen),
      explain:
        "Schema, clinical and safety checks: approved picture, difficulty in range, no answer leak, no medical claims. Failures retry once, then fall back to rules.",
      visual: gen ? <ValidationVisual gen={gen} /> : noAi,
      raw: gen?.attempts ?? null,
      ms: 6000,
    },
    {
      id: "exercise",
      lane: 1,
      title: "Exercise shown",
      concept: "Rules",
      icon: ImageIcon,
      summary: t.shown.prompt ?? "",
      state: "ok",
      explain:
        "The ExerciseIssuer re-checks every rule and a database trigger refuses anything out of range. Pictures and answers always come from the catalogue.",
      visual: <ExerciseVisual t={t} />,
      raw: t.shown,
      ms: 5000,
    },
    {
      id: "response",
      lane: 1,
      title: "Patient response",
      concept: "Rules",
      icon: MessageSquareText,
      summary: r ? `“${r.text ?? "not sure"}”` : "Not answered yet",
      state: r ? "ok" : "idle",
      explain: "The patient types, taps word tiles or speaks.",
      visual: <ResponseVisual t={t} />,
      raw: r,
      ms: 4000,
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
          ? "Transcribed on device"
          : "Typed: not needed",
      state: !r ? "idle" : r.mode === "speech" ? "ok" : "skip",
      explain:
        "Deep learning: faster-whisper (an encoder–decoder transformer) transcribes speech on this machine. Unreliable transcripts are never scored; audio is deleted.",
      visual: <SpeechVisual t={t} />,
      raw: r ? { mode: r.mode, transcript: r.text } : null,
      ms: 4500,
    },
    {
      id: "nlp",
      lane: 1,
      title: "NLP analysis",
      concept: "NLP",
      icon: Wand2,
      summary: !r
        ? "—"
        : r.concepts_matched
          ? `${r.concepts_matched.length} key ideas found`
          : (r.match_type ?? "none").replaceAll("_", " "),
      state: r ? "ok" : "idle",
      explain:
        "Normalisation, edit-distance matching, concept coverage and word-order analysis turn the answer into structured findings.",
      visual: <NLPVisual t={t} />,
      raw: r
        ? {
            match_type: r.match_type,
            concepts_matched: r.concepts_matched,
            concepts_missing: r.concepts_missing,
          }
        : null,
      ms: 4500,
    },
    {
      id: "score",
      lane: 1,
      title: "Deterministic score",
      concept: "Rules",
      icon: ClipboardCheck,
      summary: r ? `${r.outcome.replace("_", " ")} · ${r.score}` : "—",
      state: r ? "ok" : "idle",
      explain:
        "The official score comes from fixed, explainable rules. The AI never sees it before it is final, and can never change it.",
      visual: <ScoreVisual t={t} />,
      raw: r ? { outcome: r.outcome, score: r.score } : null,
      ms: 4500,
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
      state: !fb ? (r ? "skip" : "idle") : fb.output ? genState(fb) : "warn",
      explain:
        "After scoring, the LLM writes a short supportive tip (feedback_generation_v1). Tips that contradict the score are rejected.",
      visual: <FeedbackVisual gen={fb} />,
      raw: fb?.attempts ?? null,
      ms: 6000,
    },
    {
      id: "next",
      lane: 2,
      title: "Next exercise",
      concept: "Rules",
      icon: Repeat,
      summary: next
        ? `Picture ${next.position} · level ${next.difficulty}`
        : "Not issued yet",
      state: next ? "ok" : "idle",
      explain: "The updated performance feeds the next turn of the loop.",
      visual: <NextVisual next={next} />,
      raw: next
        ? {
            position: next.position,
            difficulty: next.difficulty,
            source: next.source,
          }
        : null,
      ms: 5000,
    },
  ];
}

const time = (iso: string) =>
  new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
const SHORT: Record<string, string> = {
  word_retrieval: "Word retrieval",
  sentence_formation: "Sentences",
  descriptive_language: "Description",
};

type Beam = { d: string; state: State };

export function PipelineMap({ data }: { data: Pipeline }) {
  const reduce = useReducedMotion();
  const [traceIndex, setTraceIndex] = useState(() =>
    Math.max(
      0,
      data.traces.findIndex((t) => t.response !== null),
    ),
  );
  const [selected, setSelected] = useState(0);
  const [direction, setDirection] = useState(1);
  const [playing, setPlaying] = useState(false);
  const [beams, setBeams] = useState<Beam[]>([]);
  const container = useRef<HTMLDivElement>(null);
  const nodeRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const stage = useRef<HTMLElement>(null);
  const chip = useRef<HTMLButtonElement | null>(null);

  const trace = data.traces[traceIndex];
  const steps = trace ? buildSteps(trace, data.traces[traceIndex - 1]) : [];
  const step = steps[selected];

  const go = useCallback(
    (i: number) => {
      setDirection(i >= selected ? 1 : -1);
      setSelected(i);
    },
    [selected],
  );

  const layout = useCallback(() => {
    const box = container.current?.getBoundingClientRect();
    if (!box) return;
    const out: Beam[] = [];
    for (let i = 0; i < steps.length - 1; i++) {
      const a = nodeRefs.current[i]?.getBoundingClientRect();
      const b = nodeRefs.current[i + 1]?.getBoundingClientRect();
      if (!a || !b) continue;
      let d: string;
      if (Math.abs(a.top - b.top) < 20) {
        const x1 = a.right - box.left,
          y1 = a.top + a.height / 2 - box.top;
        const x2 = b.left - box.left,
          y2 = b.top + b.height / 2 - box.top;
        d = `M${x1},${y1} C${x1 + 14},${y1} ${x2 - 14},${y2} ${x2},${y2}`;
      } else {
        const x1 = a.left + a.width / 2 - box.left,
          y1 = a.bottom - box.top;
        const x2 = b.left + b.width / 2 - box.left,
          y2 = b.top - box.top;
        const mid = (y1 + y2) / 2;
        d = `M${x1},${y1} C${x1},${mid} ${x2},${mid} ${x2},${y2}`;
      }
      out.push({ d, state: steps[i + 1].state });
    }
    setBeams(out);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [traceIndex, steps.length]);

  useLayoutEffect(() => {
    layout();
    const ro = new ResizeObserver(layout);
    if (container.current) ro.observe(container.current);
    return () => ro.disconnect();
  }, [layout]);

  // Auto-advance while playing; each slide stays up for its own duration.
  useEffect(() => {
    if (!playing || !step) return;
    const id = setTimeout(() => {
      if (selected >= steps.length - 1) setPlaying(false);
      else go(selected + 1);
    }, step.ms);
    return () => clearTimeout(id);
  }, [playing, selected, step, steps.length, go]);

  // Keep the chosen exercise visible in its scrolling row (never scroll the page).
  useEffect(() => {
    const row = chip.current?.parentElement;
    if (chip.current && row)
      row.scrollLeft = Math.max(
        0,
        chip.current.offsetLeft - row.offsetLeft - 16,
      );
  }, [traceIndex]);

  const showStage = () =>
    stage.current?.scrollIntoView({
      behavior: reduce ? "auto" : "smooth",
      block: "start",
    });

  function togglePlay() {
    if (playing) {
      setPlaying(false);
      return;
    }
    if (selected >= steps.length - 1) go(0);
    setPlaying(true);
    showStage();
  }

  if (!trace || !step) {
    return (
      <p className="text-ink-muted">
        No exercises yet. Start a practice session as the patient.
      </p>
    );
  }
  let index = -1;
  const variants = reduce
    ? { enter: { opacity: 0 }, center: { opacity: 1 }, exit: { opacity: 0 } }
    : {
        enter: (dir: number) => ({
          opacity: 0,
          x: 56 * dir,
          filter: "blur(8px)",
        }),
        center: { opacity: 1, x: 0, filter: "blur(0px)" },
        exit: (dir: number) => ({
          opacity: 0,
          x: -56 * dir,
          filter: "blur(8px)",
        }),
      };

  return (
    <div className="flex flex-col gap-6">
      {/* Exercise picker */}
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
              ref={(el) => {
                if (i === traceIndex) chip.current = el;
              }}
              type="button"
              aria-pressed={i === traceIndex}
              onClick={() => {
                setTraceIndex(i);
                go(0);
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
                    : STATE[genState(t.generation)].dot,
                )}
              />
              Picture {t.position} · {SHORT[t.objective] ?? t.objective}
              <span className="font-normal">{time(t.issued_at)}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <button
          type="button"
          onClick={togglePlay}
          className="group inline-flex min-h-14 items-center gap-3 rounded-full bg-linear-to-r from-accent to-brand-deep px-7 text-lg font-bold text-white shadow-lg shadow-accent/30 transition-transform hover:scale-[1.02]"
        >
          <span className="grid size-8 place-items-center rounded-full bg-white/20">
            {playing ? (
              <Pause aria-hidden="true" size={18} />
            ) : (
              <Play aria-hidden="true" size={18} className="translate-x-px" />
            )}
          </span>
          {playing ? "Pause" : "Play the pipeline"}
        </button>
        <ul
          aria-label="Concepts"
          className="flex flex-wrap gap-1.5 text-xs font-bold"
        >
          {(Object.keys(CONCEPT_LIGHT) as Concept[]).map((c) => (
            <li
              key={c}
              className={cn("rounded-full px-2.5 py-1", CONCEPT_LIGHT[c])}
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
        className="relative isolate overflow-hidden rounded-3xl bg-[radial-gradient(900px_420px_at_12%_-12%,rgba(94,196,182,0.30),transparent_60%),radial-gradient(700px_380px_at_100%_115%,rgba(47,94,168,0.30),transparent_60%),linear-gradient(140deg,#0d5556,#0a3d3e_45%,#062627)] p-5 text-white shadow-xl shadow-ink/20 sm:p-7"
      >
        <div
          aria-hidden="true"
          className="absolute inset-0 -z-20 bg-[radial-gradient(rgba(255,255,255,0.08)_1px,transparent_1px)] bg-size-[22px_22px]"
        />
        <svg
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 -z-10 size-full overflow-visible"
        >
          <defs>
            <filter id="beam-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          {beams.map((b, i) => {
            const active = i === selected - 1;
            const live = b.state === "ok" || b.state === "warn";
            const color = STATE[b.state].beam;
            return (
              <g key={i}>
                <path
                  d={b.d}
                  fill="none"
                  stroke="white"
                  strokeOpacity={0.12}
                  strokeWidth={active ? 7 : 4}
                  strokeLinecap="round"
                />
                <path
                  d={b.d}
                  fill="none"
                  stroke={color}
                  strokeOpacity={live ? (active ? 1 : 0.55) : 0.35}
                  strokeWidth={active ? 4 : 2.5}
                  strokeLinecap="round"
                  strokeDasharray={live ? "10 22" : "3 7"}
                  filter={live ? "url(#beam-glow)" : undefined}
                  className={
                    live ? "animate-flow motion-reduce:animate-none" : undefined
                  }
                />
                {active && !reduce && (
                  <circle r="6" fill="#d9f7f2" filter="url(#beam-glow)">
                    <animateMotion
                      dur="1.4s"
                      repeatCount="indefinite"
                      path={b.d}
                    />
                  </circle>
                )}
              </g>
            );
          })}
        </svg>

        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <p className="flex items-center gap-2 text-lg font-bold">
            <Sparkles
              aria-hidden="true"
              size={20}
              className="text-brand-glow"
            />
            RehabMind AI loop
          </p>
          <p className="rounded-full bg-white/10 px-3 py-1 text-sm text-brand-muted ring-1 ring-white/15">
            Picture {trace.position} · {trace.objective_label}
          </p>
        </div>

        <div className="flex flex-col gap-8">
          {([0, 1, 2] as const).map((lane) => (
            <section
              key={lane}
              aria-label={`Stage ${lane + 1}: ${LANES[lane].title}`}
              className="flex flex-col gap-3"
            >
              <div className="flex w-fit items-baseline gap-3 rounded-full bg-[#0a3d3e]/90 px-3 py-1 ring-1 ring-white/10">
                <h3 className="text-sm font-bold tracking-widest text-brand-glow uppercase">
                  {lane + 1} · {LANES[lane].title}
                </h3>
                <p className="hidden text-sm text-brand-muted sm:block">
                  {LANES[lane].text}
                </p>
              </div>
              <ol className="grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
                {steps
                  .filter((s) => s.lane === lane)
                  .map((s) => {
                    index += 1;
                    const i = index;
                    const Icon = s.icon;
                    const active = i === selected;
                    const done = i < selected;
                    return (
                      <li key={s.id}>
                        <button
                          ref={(el) => {
                            nodeRefs.current[i] = el;
                          }}
                          type="button"
                          aria-pressed={active}
                          onClick={() => {
                            go(i);
                            setPlaying(false);
                            stage.current?.scrollIntoView({
                              behavior: reduce ? "auto" : "smooth",
                              block: "nearest",
                            });
                          }}
                          className={cn(
                            "relative flex h-full w-full flex-col gap-2 rounded-2xl border-2 p-3.5 text-left text-ink transition-all duration-500",
                            "border-white bg-surface shadow-[0_10px_28px_-14px_rgba(0,0,0,0.65)] hover:-translate-y-0.5",
                            active &&
                              "-translate-y-1 border-[#5ec4b6] shadow-[0_0_0_4px_rgba(94,196,182,0.45),0_0_40px_-2px_rgba(94,196,182,0.9)]",
                            (s.state === "skip" || s.state === "idle") &&
                              !active &&
                              "border-dashed border-[#9fb7b3] bg-[#e8f0ee]",
                          )}
                        >
                          <span className="flex items-center justify-between gap-2">
                            <span
                              aria-hidden="true"
                              className={cn(
                                "grid size-9 place-items-center rounded-xl",
                                CONCEPT_LIGHT[s.concept],
                              )}
                            >
                              <Icon size={18} />
                            </span>
                            <span
                              className={cn(
                                "rounded-full px-2 py-0.5 text-xs font-bold",
                                CONCEPT_LIGHT[s.concept],
                              )}
                            >
                              {s.concept}
                            </span>
                          </span>
                          <span className="flex items-center gap-2 font-bold">
                            <span
                              aria-hidden="true"
                              className={cn(
                                "size-2.5 shrink-0 rounded-full",
                                DOT_ON_LIGHT[s.state],
                              )}
                            />
                            {i + 1}. {s.title}
                          </span>
                          <span className="line-clamp-1 text-sm text-ink-muted">
                            {s.summary}
                          </span>
                          {done && playing && (
                            <span
                              aria-hidden="true"
                              className="absolute top-2 right-2 size-2 rounded-full bg-success"
                            />
                          )}
                          <span className="sr-only">
                            Status: {STATE[s.state].label}
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

      {/* Presentation stage */}
      <section
        ref={stage}
        aria-labelledby="step-title"
        className="flex scroll-mt-24 flex-col gap-4"
      >
        <Rail
          steps={steps}
          selected={selected}
          onSelect={(i) => {
            go(i);
            setPlaying(false);
          }}
        />

        <div className="relative overflow-hidden rounded-3xl bg-surface shadow-xl shadow-ink/10 ring-1 ring-line">
          {playing && (
            <div
              aria-hidden="true"
              className="absolute inset-x-0 top-0 h-1.5 bg-canvas"
            >
              <div
                key={`${traceIndex}-${selected}`}
                className="h-full origin-left animate-countdown bg-linear-to-r from-accent to-[#5ec4b6]"
                style={{ animationDuration: `${step.ms}ms` }}
              />
            </div>
          )}
          <p aria-live="polite" className="sr-only">
            Step {selected + 1} of {steps.length}: {step.title},{" "}
            {STATE[step.state].label}
          </p>
          <AnimatePresence mode="popLayout" initial={false} custom={direction}>
            <motion.div
              key={`${traceIndex}-${selected}`}
              custom={direction}
              variants={variants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{
                duration: reduce ? 0.15 : 0.6,
                ease: [0.22, 1, 0.36, 1],
              }}
              className="grid min-h-[26rem] gap-8 p-6 sm:p-10 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]"
            >
              <div className="flex flex-col gap-4">
                <span
                  aria-hidden="true"
                  className="bg-linear-to-br from-[#4f9e94] to-[#5ec4b6] bg-clip-text text-7xl leading-none font-bold text-[#4f9e94]"
                >
                  {String(selected + 1).padStart(2, "0")}
                </span>
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={cn(
                      "rounded-full px-3 py-1 text-sm font-bold",
                      CONCEPT_LIGHT[step.concept],
                    )}
                  >
                    {step.concept}
                  </span>
                  <span className="flex items-center gap-1.5 text-sm text-ink-muted">
                    <span
                      aria-hidden="true"
                      className={cn(
                        "size-2.5 rounded-full",
                        step.state === "ok"
                          ? "bg-success"
                          : step.state === "warn"
                            ? "bg-[#c27c2c]"
                            : step.state === "fail"
                              ? "bg-danger"
                              : "bg-line-strong",
                      )}
                    />
                    {STATE[step.state].label}
                  </span>
                </div>
                <h3 id="step-title" className="text-3xl font-bold">
                  {step.title}
                </h3>
                <p className="text-lg text-ink-muted">{step.explain}</p>
                {step.raw != null && (
                  <details className="mt-auto rounded-xl border border-line p-3">
                    <summary className="min-h-target cursor-pointer content-center font-bold">
                      Show the raw data
                    </summary>
                    <pre
                      tabIndex={0}
                      aria-label="Raw data"
                      className="mt-2 max-h-64 overflow-auto rounded-lg bg-ink p-3 text-xs whitespace-pre-wrap text-white"
                    >
                      {typeof step.raw === "string"
                        ? step.raw
                        : JSON.stringify(step.raw, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
              <div className="min-w-0 self-center">{step.visual}</div>
            </motion.div>
          </AnimatePresence>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm font-bold text-ink-muted">
            Step {selected + 1} of {steps.length}
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={selected === 0}
              onClick={() => {
                go(selected - 1);
                setPlaying(false);
              }}
              className="inline-flex min-h-target items-center gap-1 rounded-full border-2 border-line-strong bg-surface px-4 font-bold disabled:opacity-50"
            >
              <ChevronLeft aria-hidden="true" size={18} /> Previous
            </button>
            <button
              type="button"
              onClick={togglePlay}
              className="inline-flex min-h-target items-center gap-2 rounded-full bg-accent px-5 font-bold text-white hover:bg-accent-hover"
            >
              {playing ? (
                <Pause aria-hidden="true" size={18} />
              ) : (
                <Play aria-hidden="true" size={18} />
              )}
              {playing ? "Pause" : "Play"}
            </button>
            <button
              type="button"
              disabled={selected === steps.length - 1}
              onClick={() => {
                go(selected + 1);
                setPlaying(false);
              }}
              className="inline-flex min-h-target items-center gap-1 rounded-full border-2 border-accent bg-surface px-4 font-bold text-accent disabled:opacity-50"
            >
              Next <ChevronRight aria-hidden="true" size={18} />
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}

/** All 12 steps as a progress rail: done, current, still to come. */
function Rail({
  steps,
  selected,
  onSelect,
}: {
  steps: Step[];
  selected: number;
  onSelect: (i: number) => void;
}) {
  return (
    <div
      tabIndex={0}
      aria-label="Pipeline steps"
      className="overflow-x-auto pb-1"
    >
      <ol className="relative flex min-w-[40rem] items-center justify-between px-2">
        <span
          aria-hidden="true"
          className="absolute inset-x-6 top-1/2 h-1 -translate-y-1/2 rounded-full bg-line"
        />
        <span
          aria-hidden="true"
          className="absolute top-1/2 left-6 h-1 -translate-y-1/2 rounded-full bg-linear-to-r from-accent to-[#5ec4b6] transition-[width] duration-700 ease-out"
          style={{
            width: `calc((100% - 3rem) * ${selected / (steps.length - 1)})`,
          }}
        />
        {steps.map((s, i) => {
          const Icon = s.icon;
          return (
            <li key={s.id} className="relative">
              <button
                type="button"
                onClick={() => onSelect(i)}
                aria-label={`Step ${i + 1}: ${s.title}`}
                aria-current={i === selected ? "step" : undefined}
                className={cn(
                  "grid size-11 place-items-center rounded-full border-2 transition-all duration-500",
                  i < selected && "border-accent bg-accent text-white",
                  i === selected &&
                    "scale-110 border-accent bg-surface text-accent shadow-[0_0_0_5px_rgba(15,110,110,0.18)]",
                  i > selected &&
                    "border-line-strong bg-surface text-ink-muted",
                )}
              >
                <Icon aria-hidden="true" size={18} />
              </button>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

function Stats({ traces }: { traces: Trace[] }) {
  const gens = traces
    .map((t) => t.generation)
    .filter((g): g is PipelineGeneration => !!g);
  const firstTry = gens.filter(
    (g) => g.attempts[0]?.status === "accepted",
  ).length;
  const answered = gens
    .flatMap((g) => g.attempts)
    .filter((a) => a.status !== "error");
  const latency = answered.length
    ? answered.reduce((s, a) => s + a.latency_ms, 0) / answered.length / 1000
    : null;
  const items = [
    {
      icon: Sparkles,
      label: "AI-generated exercises",
      value: `${traces.filter((t) => t.source === "ai").length} of ${traces.length}`,
    },
    {
      icon: ShieldCheck,
      label: "Valid on the first try",
      value: gens.length
        ? `${Math.round((100 * firstTry) / gens.length)}%`
        : "—",
    },
    {
      icon: Timer,
      label: "Average model time",
      value: latency === null ? "—" : `${latency.toFixed(1)} s`,
    },
    {
      icon: Lightbulb,
      label: "Feedback tips written",
      value: String(traces.filter((t) => t.feedback?.output).length),
    },
  ];
  return (
    <dl className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {items.map(({ icon: Icon, label, value }) => (
        <div
          key={label}
          className="relative flex min-h-19 flex-col-reverse justify-center rounded-2xl border border-line bg-surface py-4 pr-4 pl-18 shadow-card"
        >
          <dt className="text-sm text-ink-muted">
            <span
              aria-hidden="true"
              className="absolute top-1/2 left-4 grid size-11 -translate-y-1/2 place-items-center rounded-xl bg-linear-to-br from-accent-soft to-[#d9f7f2] text-accent-hover"
            >
              <Icon size={20} />
            </span>
            {label}
          </dt>
          <dd className="text-2xl font-bold tabular-nums">{value}</dd>
        </div>
      ))}
    </dl>
  );
}
