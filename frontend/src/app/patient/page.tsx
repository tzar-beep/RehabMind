import {
  ArrowRight,
  CalendarHeart,
  Image as ImageIcon,
  Lightbulb,
  MessageSquareText,
} from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { WeekActivity } from "@/components/patient/WeekActivity";
import {
  PracticeActivitySchema,
  PracticeStatusSchema,
} from "@/lib/api/schemas";
import { backendGet, requireRole } from "@/lib/api/server";

export const metadata: Metadata = { title: "Home" };

const STEPS = [
  {
    icon: ImageIcon,
    title: "Look at the picture",
    text: "Take as long as you need.",
  },
  {
    icon: MessageSquareText,
    title: "Give your answer",
    text: "Type it, tap the words or say it.",
  },
  {
    icon: Lightbulb,
    title: "Ask for a hint",
    text: "Hints are there whenever you want one.",
  },
];

// A few pictures from the practice library, each with its word (credits in docs/photo-credits.md).
const PREVIEW = [
  { src: "/stimuli/photos/apple_01.jpg", word: "apple" },
  { src: "/stimuli/photos/dog_01.jpg", word: "dog" },
  { src: "/stimuli/photos/cup_01.jpg", word: "cup" },
];

const today = () =>
  new Intl.DateTimeFormat("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(new Date());

export default async function PatientHome() {
  const me = await requireRole("patient");
  const [status, activity] = await Promise.all([
    backendGet("/practice/status", PracticeStatusSchema),
    backendGet("/practice/activity", PracticeActivitySchema),
  ]);

  return (
    <div className="flex flex-col gap-10">
      <section
        aria-labelledby="today-heading"
        className="grid gap-8 rounded-card bg-brand-deep p-8 text-white sm:p-10 md:grid-cols-[1fr_auto] md:items-center"
      >
        <div className="flex min-w-0 flex-col gap-3">
          <p className="flex items-center gap-2 text-base text-brand-muted">
            <CalendarHeart aria-hidden="true" size={18} />
            {today()}
          </p>
          <h1 className="text-4xl font-bold tracking-tight">
            Hello, {me.display_name}
          </h1>
          <h2 id="today-heading" className="sr-only">
            Today&rsquo;s practice
          </h2>
          {status?.has_plan ? (
            <>
              <p className="max-w-md text-xl text-brand-muted">
                {status.has_active_session
                  ? "Pick up where you left off."
                  : "A few pictures to name. Go at your own pace."}
              </p>
              <Link
                href="/patient/practice"
                className="mt-4 inline-flex min-h-16 w-fit items-center justify-center gap-3 rounded-control bg-white px-8 text-xl font-bold whitespace-nowrap text-brand-deep transition-[background-color,transform] hover:bg-accent-soft active:scale-[0.98]"
              >
                {status.has_active_session
                  ? "Continue practice"
                  : "Start practice"}
                <ArrowRight aria-hidden="true" size={24} />
              </Link>
            </>
          ) : (
            <p className="max-w-md text-xl text-brand-muted">
              Your care team is preparing your practice plan. It will appear
              here.
            </p>
          )}
        </div>

        <ul aria-hidden="true" className="hidden grid-cols-3 gap-3 md:grid">
          {PREVIEW.map((p) => (
            <li key={p.src} className="flex w-28 flex-col gap-2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={p.src}
                alt=""
                width={112}
                height={112}
                className="aspect-square w-full rounded-lg object-cover"
              />
              <span className="text-lg font-bold">{p.word}</span>
            </li>
          ))}
        </ul>
      </section>

      {activity && <WeekActivity activity={activity} />}

      <section aria-labelledby="how-heading">
        <h2 id="how-heading" className="mb-4 text-2xl font-bold">
          How practice works
        </h2>
        <ol className="grid gap-px overflow-hidden rounded-card border border-line bg-line sm:grid-cols-3">
          {STEPS.map(({ icon: Icon, title, text }) => (
            <li key={title} className="flex gap-4 bg-surface p-6 sm:flex-col">
              <Icon
                aria-hidden="true"
                size={28}
                className="shrink-0 text-accent"
              />
              <span className="flex flex-col gap-1">
                <span className="text-xl font-bold">{title}</span>
                <span className="text-ink-muted">{text}</span>
              </span>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
