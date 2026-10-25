"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api/client";
import { MoodDaySchema, type MoodDay } from "@/lib/api/schemas";
import { MOODS } from "@/lib/moods";

type Mood = MoodDay["mood"];

/** The patient's own calendar day, YYYY-MM-DD. */
const localDay = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

/** "How are you today?" in one tap. It can be changed the same day. */
export function MoodCheckin() {
  const [mood, setMood] = useState<Mood | null | undefined>(undefined);

  useEffect(() => {
    apiFetch(`/practice/mood?day=${localDay()}`, {}, MoodDaySchema.nullable())
      .then((m) => setMood(m?.mood ?? null))
      .catch(() => setMood(null));
  }, []);

  async function choose(next: Mood) {
    setMood(next);
    await apiFetch("/practice/mood", {
      method: "PUT",
      json: { mood: next, day: localDay() },
    }).catch(() => undefined);
  }

  if (mood === undefined) return null;
  return (
    <div
      role="group"
      aria-labelledby="mood-label"
      className="flex items-center gap-2"
    >
      <span id="mood-label" className="text-ink-muted">
        {mood ? "Thanks. Today:" : "How are you today?"}
      </span>
      {MOODS.map(({ mood: m, label, Icon }) => (
        <button
          key={m}
          type="button"
          aria-pressed={mood === m}
          aria-label={label}
          title={label}
          onClick={() => choose(m)}
          className={`inline-flex size-target items-center justify-center rounded-full border-2 transition-colors ${
            mood === m
              ? "border-accent bg-accent-soft text-accent-hover"
              : "border-line text-ink-muted hover:border-accent hover:text-accent"
          }`}
        >
          <Icon aria-hidden="true" size={24} />
        </button>
      ))}
    </div>
  );
}
