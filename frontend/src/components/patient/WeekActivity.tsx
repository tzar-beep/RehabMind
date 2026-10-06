import { Check, Images, Trophy } from "lucide-react";
import type { ReactNode } from "react";

import type { PracticeActivity } from "@/lib/api/schemas";
import { cn } from "@/lib/utils";

const dayKey = (d: Date) => `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;

/**
 * The patient's last seven days as a row of day markers, plus two running totals.
 * Activity only (never scores), and no "streak" pressure: a missed day is just empty.
 */
export function WeekActivity({ activity }: { activity: PracticeActivity }) {
  const practised = new Map<string, number>();
  for (const s of activity.recent) {
    if (s.answered === 0) continue;
    const k = dayKey(new Date(s.started_at));
    practised.set(k, (practised.get(k) ?? 0) + s.answered);
  }
  const today = new Date();
  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(today);
    d.setDate(today.getDate() - 6 + i);
    return { date: d, count: practised.get(dayKey(d)) ?? 0, isToday: i === 6 };
  });
  const activeDays = days.filter((d) => d.count > 0).length;
  const message = days[6].count
    ? "You practised today. Well done."
    : activeDays
      ? `You practised on ${activeDays} ${activeDays === 1 ? "day" : "days"} this week.`
      : "Every day is a fresh start.";
  const weekday = new Intl.DateTimeFormat("en-GB", { weekday: "short" });
  const full = new Intl.DateTimeFormat("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  return (
    <section
      aria-labelledby="week-heading"
      className="animate-rise grid gap-6 rounded-card [animation-delay:120ms] border border-line bg-surface p-6 shadow-card sm:p-8 lg:grid-cols-[1fr_auto]"
    >
      <div className="flex flex-col gap-5">
        <div>
          <h2 id="week-heading" className="text-2xl font-bold">
            Your week
          </h2>
          <p className="text-lg text-ink-muted">{message}</p>
        </div>
        <ol className="grid grid-cols-7 gap-2">
          {days.map(({ date, count, isToday }) => (
            <li key={dayKey(date)} className="flex flex-col items-center gap-2">
              <span
                className={cn(
                  "text-sm font-bold",
                  isToday ? "text-accent-hover" : "text-ink-muted",
                )}
              >
                <span aria-hidden="true">{weekday.format(date)}</span>
                <span className="sr-only">
                  {full.format(date)}:{" "}
                  {count
                    ? `practised ${count} ${count === 1 ? "picture" : "pictures"}`
                    : "no practice"}
                </span>
              </span>
              <span
                aria-hidden="true"
                className={cn(
                  "grid aspect-square w-full max-w-12 place-items-center rounded-full",
                  count
                    ? "bg-linear-to-br from-[#14857f] to-brand-deep text-white shadow-md shadow-accent/30"
                    : "border-2 border-dashed border-line-strong/50 bg-canvas",
                  isToday && "ring-4 ring-accent-soft",
                )}
              >
                {count > 0 && <Check size={20} strokeWidth={3} />}
              </span>
            </li>
          ))}
        </ol>
      </div>

      <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:w-64 lg:grid-cols-1">
        <Stat
          icon={<Images size={20} />}
          tile="bg-[#e5edf9] text-[#2f5ea8]"
          label="Pictures practised"
          value={activity.pictures_practised}
        />
        <Stat
          icon={<Trophy size={20} />}
          tile="bg-warning-soft text-warning"
          label="Sessions finished"
          value={activity.sessions_completed}
        />
      </dl>
    </section>
  );
}

function Stat({
  icon,
  tile,
  label,
  value,
}: {
  icon: ReactNode;
  tile: string;
  label: string;
  value: number;
}) {
  return (
    <div className="relative flex min-h-19 flex-col-reverse justify-center rounded-2xl bg-canvas py-3 pr-4 pl-19">
      <dt className="text-sm text-ink-muted">
        <span
          aria-hidden="true"
          className={`absolute top-1/2 left-4 grid size-11 -translate-y-1/2 place-items-center rounded-xl ${tile}`}
        >
          {icon}
        </span>
        {label}
      </dt>
      <dd className="text-2xl leading-tight font-bold tabular-nums">{value}</dd>
    </div>
  );
}
