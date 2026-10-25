import {
  ArrowRight,
  CalendarHeart,
  Image as ImageIcon,
  Lightbulb,
  MessageSquareText,
} from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { PictureWall } from "@/components/PictureWall";
import { DotPattern } from "@/components/magicui/dot-pattern";
import { KeepGoing } from "@/components/patient/KeepGoing";
import { PatientGoals } from "@/components/patient/PatientGoals";
import { WeekActivity } from "@/components/patient/WeekActivity";
import {
  GoalListSchema,
  PracticeActivitySchema,
  PracticeStatusSchema,
} from "@/lib/api/schemas";
import { backendGet, requireRole } from "@/lib/api/server";

export const metadata: Metadata = { title: "Home" };

const NEWCOMER_SESSIONS = 3;

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

const today = () =>
  new Intl.DateTimeFormat("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(new Date());

export default async function PatientHome() {
  const me = await requireRole("patient");
  const [status, activity, goals] = await Promise.all([
    backendGet("/practice/status", PracticeStatusSchema),
    backendGet("/practice/activity", PracticeActivitySchema),
    backendGet("/practice/goals", GoalListSchema),
  ]);

  const newcomer = (activity?.sessions_completed ?? 0) < NEWCOMER_SESSIONS;
  const cta =
    "mt-2 inline-flex min-h-14 w-full items-center justify-center gap-3 rounded-control bg-white px-8 text-xl font-bold whitespace-nowrap text-brand-deep transition-[background-color,transform] hover:bg-accent-soft active:scale-[0.98] sm:w-fit";

  // One screen, no scrolling: the welcome takes the height that is left, the practice
  // calendar keeps its own.
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 short:max-md:gap-3">
      <section
        aria-labelledby="today-heading"
        className="relative isolate flex shrink-0 flex-col gap-4 overflow-hidden rounded-card bg-brand-deep p-5 text-white sm:p-6 short:max-md:p-4 md:grid md:min-h-0 md:flex-1 md:shrink md:grid-cols-[minmax(0,1fr)_auto] md:grid-rows-[minmax(0,1fr)] md:items-center md:gap-8 lg:p-8"
      >
        {/* Static texture for depth (Magic UI Dot Pattern): no motion. */}
        <DotPattern
          aria-hidden="true"
          width={18}
          height={18}
          className="-z-10 text-white/25 [mask-image:radial-gradient(ellipse_at_top_left,white,transparent_70%)]"
        />
        <div className="flex min-w-0 flex-col gap-2">
          <p className="flex items-center gap-2 text-base text-brand-muted short:max-md:hidden">
            <CalendarHeart aria-hidden="true" size={18} />
            {today()}
          </p>
          <h1 className="text-3xl leading-tight font-bold tracking-tight sm:text-4xl">
            Hello, {me.display_name}
          </h1>
          <h2 id="today-heading" className="sr-only">
            Today&rsquo;s practice
          </h2>
          {status?.has_plan &&
          status.resumable &&
          !status.has_active_session ? (
            <KeepGoing
              sessionId={status.resumable.session_id}
              answered={status.resumable.answered}
            />
          ) : status?.has_plan ? (
            <>
              <p className="max-w-md text-xl text-brand-muted short:max-md:text-lg">
                {status.has_active_session
                  ? "Pick up where you left off."
                  : "A few pictures to name. Go at your own pace."}
              </p>
              <Link href="/patient/practice" className={cta}>
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
          {/* For newcomers only: how practice works, in three short steps. */}
          {newcomer && (
            <ol
              aria-label="How practice works"
              className="mt-3 flex flex-col gap-2 text-brand-muted"
            >
              {STEPS.map(({ icon: Icon, title, text }) => (
                <li key={title} className="flex items-center gap-3">
                  <Icon aria-hidden="true" size={20} className="shrink-0" />
                  <span>
                    <strong className="text-white">{title}.</strong> {text}
                  </span>
                </li>
              ))}
            </ol>
          )}
        </div>

        {/* With goals, the right side is what the patient is working towards; without,
            the picture wall is a second way into practice. */}
        {goals && goals.length > 0 ? (
          <PatientGoals goals={goals} />
        ) : (
          <>
            {/* A second, larger way into practice (the button stays the accessible one). */}
            <Link
              href={status?.has_plan ? "/patient/practice" : "#"}
              aria-hidden="true"
              tabIndex={-1}
              className={`hidden h-full max-h-72 min-h-0 md:block ${
                status?.has_plan
                  ? "transition-opacity hover:opacity-90"
                  : "pointer-events-none"
              }`}
            >
              <PictureWall fill className="aspect-[3/2] h-full grid-rows-2" />
            </Link>
          </>
        )}
      </section>

      {activity && <WeekActivity activity={activity} />}
      <Link
        href="/credits"
        className="-my-2 inline-flex min-h-target shrink-0 items-center self-start text-sm text-ink-muted underline underline-offset-4 sm:hidden short:hidden"
      >
        Photo credits
      </Link>
    </div>
  );
}
