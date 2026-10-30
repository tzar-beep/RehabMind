"use client";

import {
  HeatmapCells,
  HeatmapChart,
  type HeatmapColumn,
  HeatmapInteractionBoundary,
  HeatmapInteractionProvider,
  HeatmapLegend,
  HeatmapTooltip,
  HeatmapXAxis,
  HeatmapYAxis,
} from "@/components/charts/heatmap";
import type { PracticeActivity } from "@/lib/api/schemas";

export const CALENDAR_WEEKS = 16;

const dayKey = (d: Date) => `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;

/** Pictures in a day → shade (0 = no practice). Thresholds keep one short session visible. */
function level(pictures: number): number {
  if (pictures <= 0) return 0;
  if (pictures <= 5) return 1;
  if (pictures <= 10) return 2;
  if (pictures <= 20) return 3;
  return 4;
}

/** Monday of the week containing `d`, at midnight local time. */
export function weekStart(d: Date): Date {
  const m = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  m.setDate(m.getDate() - ((m.getDay() + 6) % 7));
  return m;
}

/** Pictures practised per local day, from the activity sessions. */
export function picturesByDay(activity: PracticeActivity): Map<string, number> {
  const byDay = new Map<string, number>();
  for (const s of activity.recent) {
    const k = dayKey(new Date(s.started_at));
    byDay.set(k, (byDay.get(k) ?? 0) + s.answered);
  }
  return byDay;
}

/**
 * The patient's practice as a calendar of days (columns are weeks, Monday at the top).
 * Activity only, never scores, and no streak to break: an empty day is just empty.
 */
export function PracticeCalendar({
  activity,
  name,
}: {
  activity: PracticeActivity;
  name?: string;
}) {
  const byDay = picturesByDay(activity);
  const today = new Date();
  const first = weekStart(today);
  first.setDate(first.getDate() - 7 * (CALENDAR_WEEKS - 1));
  const columns: HeatmapColumn[] = Array.from(
    { length: CALENDAR_WEEKS },
    (_, w) => ({
      bin: w,
      bins: Array.from({ length: 7 }, (_, d) => {
        const date = new Date(first);
        date.setDate(first.getDate() + w * 7 + d);
        return { bin: d, date, count: level(byDay.get(dayKey(date)) ?? 0) };
      }).filter((b) => b.date <= today),
    }),
  );
  const days = [...byDay.values()].filter((n) => n > 0).length;

  return (
    <figure className="flex min-h-0 flex-col gap-1">
      <figcaption className="sr-only">
        Practice calendar for the last {CALENDAR_WEEKS} weeks: {name ?? "you"}{" "}
        practised on {days} {days === 1 ? "day" : "days"}.
      </figcaption>
      <div aria-hidden="true" className="h-28 w-full short:max-md:h-24">
        <HeatmapInteractionProvider>
          <HeatmapInteractionBoundary>
            <HeatmapChart
              data={columns}
              layout="fill"
              gap={3}
              margin={{ top: 18, right: 0, bottom: 0, left: 28 }}
            >
              <HeatmapXAxis />
              <HeatmapYAxis labelFormat="initial" />
              <HeatmapCells cornerRadius={3} />
              <HeatmapTooltip
                formatLabel={(_, date) => {
                  const n = byDay.get(dayKey(date)) ?? 0;
                  return n
                    ? `${n} ${n === 1 ? "picture" : "pictures"}`
                    : "No practice";
                }}
              />
            </HeatmapChart>
          </HeatmapInteractionBoundary>
        </HeatmapInteractionProvider>
      </div>
      <div aria-hidden="true" className="self-end short:max-md:hidden">
        <HeatmapLegend />
      </div>
    </figure>
  );
}
