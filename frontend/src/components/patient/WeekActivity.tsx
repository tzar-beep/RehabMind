"use client";

import type { PracticeActivity } from "@/lib/api/schemas";

import { PracticeCalendar, picturesByDay } from "./PracticeCalendar";

const dayKey = (d: Date) => `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;

/**
 * The patient's practice: a calendar of the last weeks and two running totals. Activity
 * only (never scores), and no "streak" pressure: a missed day is just empty. A client
 * component so "today" is the patient's own day, not the server's.
 */
export function WeekActivity({ activity }: { activity: PracticeActivity }) {
  const byDay = picturesByDay(activity);
  const today = new Date();
  const thisWeek = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    return byDay.get(dayKey(d)) ?? 0;
  });
  const activeDays = thisWeek.filter((n) => n > 0).length;
  const message = thisWeek[0]
    ? "You practised today. Well done."
    : activeDays
      ? `You practised on ${activeDays} ${activeDays === 1 ? "day" : "days"} this week.`
      : "Every day is a fresh start.";

  return (
    <section
      aria-labelledby="week-heading"
      className="grid shrink-0 gap-x-8 gap-y-3 rounded-card border border-line bg-surface p-4 sm:p-5 md:grid-cols-[minmax(0,1fr)_auto] short:max-md:gap-y-2"
    >
      <div className="flex min-w-0 flex-col gap-2">
        <div className="flex flex-wrap items-baseline gap-x-3">
          <h2 id="week-heading" className="text-xl font-bold">
            Your practice
          </h2>
          <p className="text-ink-muted">{message}</p>
        </div>
        <PracticeCalendar activity={activity} />
      </div>
      <dl className="grid grid-cols-2 gap-3 md:w-44 md:grid-cols-1 md:content-center short:max-md:grid-cols-1 short:max-md:gap-0">
        <Stat label="Pictures practised" value={activity.pictures_practised} />
        <Stat label="Sessions finished" value={activity.sessions_completed} />
      </dl>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex flex-col-reverse short:max-md:flex-row-reverse short:max-md:items-baseline short:max-md:justify-end short:max-md:gap-2">
      <dt className="text-ink-muted">{label}</dt>
      <dd className="text-3xl leading-tight font-bold tabular-nums short:max-md:text-xl">
        {value}
      </dd>
    </div>
  );
}
