import {
  ArrowRight,
  CalendarHeart,
  Image as ImageIcon,
  Lightbulb,
  MessageSquareText,
} from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { PracticeStatusSchema } from "@/lib/api/schemas";
import { backendGet, requireRole } from "@/lib/api/server";

export const metadata: Metadata = { title: "Home" };

const STEPS = [
  {
    icon: ImageIcon,
    tile: "bg-accent-soft text-accent-hover",
    title: "Look at the picture",
    text: "Take as long as you need.",
  },
  {
    icon: MessageSquareText,
    tile: "bg-[#e5edf9] text-[#2f5ea8]",
    title: "Give your answer",
    text: "Type it, tap the words or say it.",
  },
  {
    icon: Lightbulb,
    tile: "bg-warning-soft text-warning",
    title: "Ask for a hint",
    text: "Hints are there whenever you want one.",
  },
];

// Decorative collage from the practice photo library (credits in docs/photo-credits.md).
const COLLAGE = [
  { src: "/stimuli/photos/apple_01.jpg", cls: "left-0 top-6 -rotate-6" },
  { src: "/stimuli/photos/dog_01.jpg", cls: "left-24 top-0 rotate-3 z-10" },
  { src: "/stimuli/photos/cup_01.jpg", cls: "left-12 top-28 rotate-2" },
];

const today = () =>
  new Intl.DateTimeFormat("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(new Date());

export default async function PatientHome() {
  const me = await requireRole("patient");
  const status = await backendGet("/practice/status", PracticeStatusSchema);

  return (
    <div className="flex flex-col gap-10">
      <section
        aria-labelledby="today-heading"
        className="relative isolate overflow-hidden rounded-card bg-linear-to-br from-[#0d5556] via-brand-deep to-[#072b2c] p-8 text-white shadow-card sm:p-10"
      >
        {/* Soft static light shapes for depth. */}
        <div
          aria-hidden="true"
          className="absolute -top-24 -right-16 -z-10 size-72 rounded-full bg-[#5ec4b6]/20 blur-3xl"
        />
        <div
          aria-hidden="true"
          className="absolute -bottom-28 left-10 -z-10 size-64 rounded-full bg-[#14857f]/30 blur-3xl"
        />

        <div className="flex items-center gap-8">
          <div className="flex min-w-0 flex-1 flex-col gap-3">
            <p className="flex items-center gap-2 text-base text-brand-muted">
              <CalendarHeart aria-hidden="true" size={18} />
              {today()}
            </p>
            <h1 className="text-4xl font-bold sm:text-5xl">
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
                  className="mt-4 inline-flex min-h-16 w-fit items-center justify-center gap-3 rounded-control bg-white px-8 text-xl font-bold text-brand-deep shadow-lg shadow-black/20 transition-colors hover:bg-accent-soft"
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

          <div
            aria-hidden="true"
            className="relative hidden h-56 w-60 shrink-0 md:block"
          >
            {COLLAGE.map((p) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                key={p.src}
                src={p.src}
                alt=""
                width={136}
                height={136}
                className={`absolute size-34 rounded-2xl border-4 border-white object-cover shadow-xl shadow-black/30 ${p.cls}`}
              />
            ))}
          </div>
        </div>
      </section>

      <section aria-labelledby="how-heading">
        <h2 id="how-heading" className="mb-4 text-2xl font-bold">
          How practice works
        </h2>
        <ol className="grid gap-4 sm:grid-cols-3">
          {STEPS.map(({ icon: Icon, tile, title, text }, i) => (
            <li
              key={title}
              className="relative flex gap-4 overflow-hidden rounded-card border border-line bg-surface p-6 shadow-card sm:flex-col"
            >
              <span
                aria-hidden="true"
                className="absolute top-3 right-5 text-6xl leading-none font-bold text-line/70"
              >
                {i + 1}
              </span>
              <span
                aria-hidden="true"
                className={`grid size-14 shrink-0 place-items-center rounded-2xl ${tile}`}
              >
                <Icon size={28} />
              </span>
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
