"use client";

import { Lightbulb } from "lucide-react";
import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api/client";
import { AIFeedbackSchema } from "@/lib/api/schemas";

type Tip = { feedback: string; hint: string | null };

/**
 * A personal tip about the answer just given, written by the local language model after
 * the answer was scored. Loads after the standard feedback is on screen, so a slow or
 * unavailable model never delays the patient; if nothing valid comes back, nothing shows.
 */
export function AiTip({ exerciseId }: { exerciseId: string }) {
  const [tip, setTip] = useState<Tip | null | "loading">("loading");

  useEffect(() => {
    let live = true;
    apiFetch(
      `/practice/exercises/${exerciseId}/feedback`,
      { method: "POST" },
      AIFeedbackSchema,
    )
      .then((r) => {
        if (live)
          setTip(r?.feedback ? { feedback: r.feedback, hint: r.hint } : null);
      })
      .catch(() => live && setTip(null));
    return () => {
      live = false;
    };
  }, [exerciseId]);

  if (tip === null) return null;
  if (tip === "loading") {
    return (
      <p
        aria-hidden="true"
        className="text-base text-ink-muted motion-safe:animate-pulse"
      >
        Preparing a tip for you…
      </p>
    );
  }
  return (
    <div
      role="status"
      className="animate-rise flex w-full max-w-xl gap-4 rounded-card border border-accent/20 bg-accent-soft px-6 py-5 text-left"
    >
      <span
        aria-hidden="true"
        className="grid size-11 shrink-0 place-items-center rounded-full bg-surface text-warning shadow-sm"
      >
        <Lightbulb size={22} />
      </span>
      <div className="flex flex-col gap-1">
        <p className="text-sm font-bold text-accent-hover">A tip for you</p>
        <p className="text-xl">{tip.feedback}</p>
        {tip.hint && <p className="text-lg text-ink-muted">{tip.hint}</p>}
      </div>
    </div>
  );
}
