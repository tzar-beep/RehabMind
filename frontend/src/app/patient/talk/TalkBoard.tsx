"use client";

import {
  Angry,
  Armchair,
  Bath,
  BedDouble,
  CircleHelp,
  Coffee,
  Frown,
  Hand,
  Heart,
  HeartCrack,
  Maximize2,
  Meh,
  Phone,
  RefreshCw,
  Smile,
  Snowflake,
  Sun,
  ThumbsDown,
  ThumbsUp,
  Timer,
  Turtle,
  Utensils,
  Volume2,
  X,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";

import type { PersonalWord } from "@/lib/api/schemas";
import { say, useCanSpeak } from "@/lib/speak";

type Tile = { label: string; say: string; Icon?: LucideIcon; image?: string };

// Short, everyday phrases: tap a picture and the device says it.
const BOARDS: { id: string; label: string; tiles: Tile[] }[] = [
  {
    id: "needs",
    label: "Needs",
    tiles: [
      {
        label: "Drink",
        say: "I'm thirsty. Can I have a drink, please?",
        Icon: Coffee,
      },
      { label: "Food", say: "I'm hungry.", Icon: Utensils },
      { label: "Toilet", say: "I need the toilet, please.", Icon: Bath },
      { label: "Tired", say: "I'm tired. I need a rest.", Icon: BedDouble },
      { label: "Pain", say: "I'm in pain.", Icon: HeartCrack },
      { label: "Too cold", say: "I'm cold.", Icon: Snowflake },
      { label: "Too hot", say: "I'm too hot.", Icon: Sun },
      { label: "Sit down", say: "I'd like to sit down.", Icon: Armchair },
      {
        label: "Phone",
        say: "Can you call someone for me, please?",
        Icon: Phone,
      },
    ],
  },
  {
    id: "feelings",
    label: "Feelings",
    tiles: [
      { label: "Happy", say: "I'm happy.", Icon: Smile },
      { label: "Sad", say: "I feel sad.", Icon: Frown },
      { label: "Okay", say: "I'm okay.", Icon: Meh },
      {
        label: "Frustrated",
        say: "I'm frustrated. I know what I want to say.",
        Icon: Angry,
      },
      { label: "Worried", say: "I'm worried.", Icon: CircleHelp },
      { label: "Love you", say: "I love you.", Icon: Heart },
    ],
  },
  {
    id: "answers",
    label: "Answers",
    tiles: [
      { label: "Yes", say: "Yes.", Icon: ThumbsUp },
      { label: "No", say: "No.", Icon: ThumbsDown },
      { label: "I don't know", say: "I don't know.", Icon: CircleHelp },
      { label: "Wait", say: "Please wait. Give me a moment.", Icon: Timer },
      {
        label: "Say again",
        say: "Can you say that again, please?",
        Icon: RefreshCw,
      },
      { label: "Slower", say: "Please speak more slowly.", Icon: Turtle },
      { label: "Stop", say: "Please stop.", Icon: Hand },
    ],
  },
];

/**
 * A communication board for everyday use: big pictures that speak a phrase when tapped,
 * and the patient's own people and things. Nothing is recorded or sent anywhere.
 */
export function TalkBoard({ ownWords }: { ownWords: PersonalWord[] }) {
  const speakable = useCanSpeak();
  const boards = ownWords.length
    ? [
        ...BOARDS,
        {
          id: "mine",
          label: "My people & things",
          tiles: ownWords.map((w): Tile => ({
            label: w.word,
            say: w.word,
            image: w.image_url,
          })),
        },
      ]
    : BOARDS;
  const [boardId, setBoardId] = useState(boards[0].id);
  const [spoken, setSpoken] = useState<string | null>(null);
  const [big, setBig] = useState(false);
  const board = boards.find((b) => b.id === boardId) ?? boards[0];

  function speak(text: string) {
    setSpoken(text);
    if (speakable) say(text, 0.9);
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 sm:gap-4">
      {/* What was said last, large enough to show to someone. */}
      <div
        aria-live="polite"
        className="flex min-h-16 shrink-0 items-center gap-3 rounded-card border border-line bg-surface shadow-card px-4 py-2"
      >
        <Volume2
          aria-hidden="true"
          size={22}
          className="shrink-0 text-accent"
        />
        <p className="min-w-0 flex-1 truncate text-2xl font-bold">
          {spoken ?? (
            <span className="text-lg font-normal text-ink-muted">
              Tap a picture to say it out loud.
            </span>
          )}
        </p>
        {spoken && (
          <>
            <button
              type="button"
              onClick={() => speak(spoken)}
              className="inline-flex min-h-target items-center gap-2 rounded-control border-2 border-accent px-3 font-bold text-accent hover:bg-accent-soft"
            >
              <RefreshCw aria-hidden="true" size={18} />
              Say again
            </button>
            <button
              type="button"
              onClick={() => setBig(true)}
              className="inline-flex min-h-target items-center gap-2 rounded-control border-2 border-line-strong px-3 font-bold hover:bg-canvas"
            >
              <Maximize2 aria-hidden="true" size={18} />
              Show big
            </button>
          </>
        )}
      </div>

      <div
        role="tablist"
        aria-label="Boards"
        className="flex shrink-0 flex-wrap gap-2"
      >
        {boards.map((b) => (
          <button
            key={b.id}
            type="button"
            role="tab"
            aria-selected={b.id === board.id}
            onClick={() => setBoardId(b.id)}
            className={`min-h-target rounded-full px-5 text-lg font-bold transition-colors ${
              b.id === board.id
                ? "bg-accent text-white"
                : "border-2 border-line-strong bg-surface hover:bg-canvas"
            }`}
          >
            {b.label}
          </button>
        ))}
      </div>

      <div
        role="tabpanel"
        aria-label={board.label}
        className="grid min-h-0 flex-1 auto-rows-fr grid-cols-3 gap-2 overflow-y-auto sm:gap-3 lg:grid-cols-5"
      >
        {board.tiles.map((t) => (
          <button
            key={t.label}
            type="button"
            onClick={() => speak(t.say)}
            className="flex min-h-24 flex-col items-center justify-center gap-2 rounded-card border-2 border-line bg-surface p-2 text-center transition-[border-color,transform] hover:border-accent active:scale-[0.97]"
          >
            {t.image ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={t.image}
                alt=""
                className="size-14 rounded-control object-cover sm:size-16"
              />
            ) : (
              t.Icon && (
                <t.Icon
                  aria-hidden="true"
                  size={36}
                  strokeWidth={1.75}
                  className="text-accent"
                />
              )
            )}
            <span className="text-lg leading-tight font-bold">{t.label}</span>
          </button>
        ))}
      </div>

      {big && spoken && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Shown big"
          className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-8 bg-surface p-8"
        >
          <p className="max-w-5xl text-center text-5xl leading-tight font-bold sm:text-7xl">
            {spoken}
          </p>
          <button
            type="button"
            autoFocus
            onClick={() => setBig(false)}
            className="inline-flex min-h-target items-center gap-2 rounded-control border-2 border-line-strong px-6 text-xl font-bold hover:bg-canvas"
          >
            <X aria-hidden="true" size={22} />
            Close
          </button>
        </div>
      )}
    </div>
  );
}
