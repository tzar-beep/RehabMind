"use client";

import { Volume2 } from "lucide-react";
import { useState } from "react";

import { say, useCanSpeak } from "@/lib/speak";

export { say, useCanSpeak };

/**
 * The word to say or to find, large, with a button to hear it. With `listenFirst` (word
 * repetition answered by typing) the word is heard, not read: showing it would turn
 * repetition into copying. It can still be shown on request.
 */
export function WordCard({
  word,
  listenFirst = false,
}: {
  word: string;
  listenFirst?: boolean;
}) {
  const speakable = useCanSpeak();
  const [revealed, setRevealed] = useState(false);
  const hidden = listenFirst && speakable && !revealed;
  return (
    <div className="flex flex-wrap items-center justify-center gap-4 rounded-card border border-line bg-surface shadow-card px-6 py-5 lg:justify-start">
      {hidden ? (
        <span className="text-xl text-ink-muted">Listen to the word.</span>
      ) : (
        <span
          lang="en"
          className="text-4xl font-bold tracking-tight sm:text-5xl"
        >
          {word}
        </span>
      )}
      {speakable && (
        <button
          type="button"
          onClick={() => say(word)}
          className="inline-flex min-h-target items-center gap-2 rounded-control border-2 border-accent px-4 font-bold text-accent transition-colors hover:bg-accent-soft"
        >
          <Volume2 aria-hidden="true" size={22} />
          Hear it
        </button>
      )}
      {hidden && (
        <button
          type="button"
          onClick={() => setRevealed(true)}
          className="inline-flex min-h-target items-center px-3 font-bold text-ink-muted underline underline-offset-4 hover:text-ink"
        >
          Show the word
        </button>
      )}
    </div>
  );
}

/**
 * Pictures to choose from. Alt text is a position, never the word: naming the picture
 * would give the answer away (the same rule as every exercise picture).
 */
export function ChoiceGrid({
  options,
  busy,
  onPick,
}: {
  options: { word: string; image_url: string }[];
  busy: boolean;
  onPick: (word: string) => void;
}) {
  return (
    <ul className="grid grid-cols-2 gap-3 lg:min-h-0 lg:flex-1 lg:grid-rows-2">
      {options.map((o, i) => (
        <li key={o.image_url} className="lg:min-h-0">
          <button
            type="button"
            disabled={busy}
            onClick={() => onPick(o.word)}
            className="block aspect-square w-full overflow-hidden rounded-card border-2 border-line bg-white p-3 lg:aspect-auto lg:h-full transition-[border-color,transform] hover:border-accent active:scale-[0.98] disabled:opacity-60"
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={o.image_url}
              alt={`Picture ${i + 1} of ${options.length}`}
              className="size-full object-contain"
            />
          </button>
        </li>
      ))}
    </ul>
  );
}
