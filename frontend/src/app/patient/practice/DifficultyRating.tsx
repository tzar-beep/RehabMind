"use client";

import { Feather, Mountain, ThumbsUp, type LucideIcon } from "lucide-react";
import { useState } from "react";

import { apiFetch } from "@/lib/api/client";

type Rating = "too_easy" | "just_right" | "too_hard";

const OPTIONS: { value: Rating; label: string; icon: LucideIcon }[] = [
  { value: "too_easy", label: "Too easy", icon: Feather },
  { value: "just_right", label: "Just right", icon: ThumbsUp },
  { value: "too_hard", label: "Too hard", icon: Mountain },
];

/**
 * One-tap, picture-supported rating of how hard the session felt. Optional: the patient
 * can ignore it. It tells the care team whether practice was at the right level.
 */
export function DifficultyRating({ sessionId }: { sessionId: string }) {
  const [chosen, setChosen] = useState<Rating | null>(null);
  const [failed, setFailed] = useState(false);

  async function rate(value: Rating) {
    setChosen(value);
    setFailed(false);
    try {
      await apiFetch(`/practice/sessions/${sessionId}/rating`, {
        method: "PUT",
        json: { rating: value },
      });
    } catch {
      setFailed(true);
    }
  }

  return (
    <fieldset className="flex w-full max-w-xl flex-col items-center gap-2">
      <legend className="mb-2 text-xl font-bold sm:text-2xl">
        How did that feel?
      </legend>
      <div className="grid w-full grid-cols-3 gap-3">
        {OPTIONS.map(({ value, label, icon: Icon }) => (
          <button
            key={value}
            type="button"
            aria-pressed={chosen === value}
            onClick={() => rate(value)}
            className={`flex min-h-20 flex-col items-center justify-center gap-1.5 rounded-card border-2 px-2 py-2 text-lg font-bold short:min-h-16 transition-colors ${
              chosen === value
                ? "border-accent bg-accent-soft text-accent-hover"
                : "border-line-strong bg-surface hover:bg-accent-soft"
            }`}
          >
            <Icon aria-hidden="true" size={28} />
            {label}
          </button>
        ))}
      </div>
      <p role="status" className="min-h-7 text-lg text-ink-muted">
        {failed
          ? "That didn't save. You can try again."
          : chosen
            ? "Thank you. Your care team will see this."
            : ""}
      </p>
    </fieldset>
  );
}
