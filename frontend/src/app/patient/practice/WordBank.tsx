"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";

/**
 * Sentence construction by tapping: each tap moves a word into the sentence; tapping a
 * placed word puts it back. Everything is a real button, so it works with a keyboard
 * and screen reader as well as touch.
 */
export function WordBank({
  words,
  busy,
  error,
  onCheck,
  onSkip,
}: {
  words: string[];
  busy: boolean;
  error: string | null;
  onCheck: (sentence: string) => void;
  onSkip: () => void;
}) {
  // Indices into `words`, in the order the patient placed them.
  const [placed, setPlaced] = useState<number[]>([]);
  const remaining = words
    .map((w, i) => ({ w, i }))
    .filter(({ i }) => !placed.includes(i));

  return (
    <div className="flex flex-col gap-3">
      <section aria-labelledby="sentence-label" className="flex flex-col">
        {/* Clear acts on the sentence, so it sits with it. */}
        <div className="flex items-center justify-between gap-3">
          <p id="sentence-label" className="text-sm font-bold text-ink-muted">
            Your sentence
          </p>
          <Button
            variant="quiet"
            disabled={busy || !placed.length}
            onClick={() => setPlaced([])}
          >
            Clear
          </Button>
        </div>
        <div
          aria-live="polite"
          className="flex min-h-16 flex-wrap items-center gap-2 rounded-card border-2 border-dashed border-line-strong bg-surface p-2"
        >
          {placed.length === 0 ? (
            <span className="px-2 text-lg text-ink-muted">
              Tap the words below.
            </span>
          ) : (
            placed.map((i, pos) => (
              <Button
                key={i}
                variant="secondary"
                onClick={() => setPlaced(placed.filter((p) => p !== i))}
                aria-label={`${words[i]}, word ${pos + 1}. Tap to remove.`}
                className="text-xl"
              >
                {words[i]}
              </Button>
            ))
          )}
        </div>
      </section>

      <section aria-labelledby="bank-label" className="flex flex-col gap-1.5">
        <p
          id="bank-label"
          className="text-sm font-bold text-ink-muted short:sr-only"
        >
          Words
        </p>
        <div className="flex flex-wrap gap-2">
          {remaining.map(({ w, i }) => (
            <Button
              key={i}
              onClick={() => setPlaced([...placed, i])}
              className="text-xl"
              aria-label={`Add ${w}`}
            >
              {w}
            </Button>
          ))}
          {remaining.length === 0 && (
            <span className="text-ink-muted">All words used.</span>
          )}
        </div>
      </section>

      {error && (
        <p role="alert" className="font-bold text-danger">
          {error}
        </p>
      )}

      {/* One row at every size: the main action takes the spare width. */}
      <div className="flex gap-2">
        <Button
          size="lg"
          busy={busy}
          className="flex-1"
          onClick={() => onCheck(placed.map((i) => words[i]).join(" "))}
        >
          Check
        </Button>
        <Button variant="secondary" size="lg" disabled={busy} onClick={onSkip}>
          I&rsquo;m not sure
        </Button>
      </div>
    </div>
  );
}
