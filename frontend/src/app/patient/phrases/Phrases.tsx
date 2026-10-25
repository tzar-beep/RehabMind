"use client";

import {
  ArrowLeft,
  Check,
  Coffee,
  Ear,
  Hand,
  Home,
  Mic,
  Phone,
  RefreshCw,
  ShoppingBasket,
  Stethoscope,
  Users,
  Volume2,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { apiFetch } from "@/lib/api/client";
import type { Script } from "@/lib/api/schemas";
import { say, useCanSpeak } from "@/lib/speak";

const ICONS: Record<string, LucideIcon> = {
  coffee: Coffee,
  phone: Phone,
  hand: Hand,
  stethoscope: Stethoscope,
  shopping: ShoppingBasket,
  home: Home,
};

// Each line: hear it, say it together with the device, then say it alone.
const STEPS = [
  { id: "listen", label: "Listen", Icon: Ear, hint: "Listen to the line." },
  {
    id: "together",
    label: "Together",
    Icon: Users,
    hint: "Say it with me, at the same time.",
  },
  {
    id: "alone",
    label: "Your turn",
    Icon: Mic,
    hint: "Now say it on your own.",
  },
] as const;

type Step = (typeof STEPS)[number]["id"];

/** The list of everyday scripts, then one script line by line. */
export function Phrases({ scripts }: { scripts: Script[] }) {
  const [open, setOpen] = useState<Script | null>(null);
  if (open) return <Practise script={open} onExit={() => setOpen(null)} />;
  return (
    <ul className="grid min-h-0 flex-1 auto-rows-fr grid-cols-2 gap-3 overflow-y-auto lg:grid-cols-3">
      {scripts.map((s) => {
        const Icon = ICONS[s.icon] ?? Volume2;
        return (
          <li key={s.id}>
            <button
              type="button"
              onClick={() => setOpen(s)}
              className="flex size-full min-h-28 flex-col items-start justify-between gap-3 rounded-card border-2 border-line bg-surface p-5 text-left transition-[border-color,transform] hover:border-accent active:scale-[0.98]"
            >
              <Icon aria-hidden="true" size={32} className="text-accent" />
              <span className="flex flex-col gap-1">
                <span className="text-xl font-bold">{s.title}</span>
                <span className="text-sm text-ink-muted">
                  {s.lines.length} lines
                  {s.times_practised > 0 &&
                    ` · practised ${s.times_practised} ${s.times_practised === 1 ? "time" : "times"}`}
                </span>
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

function Practise({ script, onExit }: { script: Script; onExit: () => void }) {
  const speakable = useCanSpeak();
  const [line, setLine] = useState(0);
  const [step, setStep] = useState<Step>("listen");
  const [said, setSaid] = useState(0);
  const [finished, setFinished] = useState(false);
  const text = script.lines[line];

  // Hearing the line is the first step; together, it is said slowly with the patient.
  useEffect(() => {
    if (!speakable || finished) return;
    if (step === "listen") say(text, 0.85);
    if (step === "together") say(text, 0.65);
  }, [step, text, speakable, finished]);

  async function next(saidIt: boolean) {
    const total = said + (saidIt ? 1 : 0);
    setSaid(total);
    if (line + 1 < script.lines.length) {
      setLine(line + 1);
      setStep("listen");
      return;
    }
    setFinished(true);
    await apiFetch(`/practice/phrases/${script.id}/done`, {
      method: "POST",
      json: { lines_said: total },
    }).catch(() => undefined);
  }

  if (finished) {
    return (
      <div className="flex min-h-0 flex-1 flex-col items-center justify-center gap-5 rounded-card border border-line bg-surface p-8 text-center">
        <Check
          aria-hidden="true"
          size={48}
          className="rounded-full bg-success-soft p-2 text-success"
        />
        <h2 className="text-3xl font-bold">{script.title}: done</h2>
        <p className="text-xl">
          You said {said} of {script.lines.length} lines.
        </p>
        <p className="max-w-md text-lg text-ink-muted">
          Try it in real life this week, then practise it again.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Button
            size="lg"
            onClick={() => {
              setLine(0);
              setStep("listen");
              setSaid(0);
              setFinished(false);
            }}
          >
            <RefreshCw aria-hidden="true" size={20} />
            Practise again
          </Button>
          <Button size="lg" variant="secondary" onClick={onExit}>
            All phrases
          </Button>
        </div>
      </div>
    );
  }

  const current = STEPS.find((s) => s.id === step)!;
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 rounded-card border border-line bg-surface p-5 sm:p-8">
      <div className="flex items-center justify-between gap-3">
        <Button variant="quiet" onClick={onExit}>
          <ArrowLeft aria-hidden="true" size={18} />
          All phrases
        </Button>
        <p className="text-lg text-ink-muted">
          {script.title} · line {line + 1} of {script.lines.length}
        </p>
      </div>

      <ol aria-label="Steps" className="flex justify-center gap-2">
        {STEPS.map((s) => (
          <li
            key={s.id}
            aria-current={s.id === step ? "step" : undefined}
            className={`flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-bold ${
              s.id === step
                ? "bg-accent text-white"
                : "bg-canvas text-ink-muted"
            }`}
          >
            <s.Icon aria-hidden="true" size={16} />
            {s.label}
          </li>
        ))}
      </ol>

      <div className="flex min-h-0 flex-1 flex-col items-center justify-center gap-4 text-center">
        <p role="status" className="text-lg text-ink-muted">
          {current.hint}
        </p>
        <p
          lang="en"
          className="max-w-3xl text-4xl leading-tight font-bold sm:text-5xl"
        >
          {text}
        </p>
        {speakable && step !== "alone" && (
          <Button
            variant="secondary"
            onClick={() => say(text, step === "together" ? 0.65 : 0.85)}
          >
            <Volume2 aria-hidden="true" size={20} />
            Hear it again
          </Button>
        )}
      </div>

      <div className="flex flex-wrap justify-center gap-3">
        {step === "listen" && (
          <Button size="lg" onClick={() => setStep("together")}>
            Say it together
          </Button>
        )}
        {step === "together" && (
          <Button size="lg" onClick={() => setStep("alone")}>
            My turn
          </Button>
        )}
        {step === "alone" && (
          <>
            <Button size="lg" onClick={() => next(true)}>
              <Check aria-hidden="true" size={20} />I said it
            </Button>
            <Button size="lg" variant="secondary" onClick={() => next(false)}>
              Not yet
            </Button>
          </>
        )}
      </div>
    </div>
  );
}
