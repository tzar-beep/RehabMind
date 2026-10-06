"use client";

import { curveMonotoneX } from "@visx/curve";
import { useId, type ReactNode } from "react";

import { Bar } from "@/components/charts/bar";
import { BarChart } from "@/components/charts/bar-chart";
import { BarXAxis } from "@/components/charts/bar-x-axis";
import { Grid } from "@/components/charts/grid";
import {
  Legend,
  LegendItem,
  LegendLabel,
  LegendMarker,
  LegendValue,
} from "@/components/charts/legend";
import { Line, LineChart } from "@/components/charts/line-chart";
import { ChartTooltip } from "@/components/charts/tooltip";
import { YAxis } from "@/components/charts/y-axis";
import type { TrendPoint } from "@/lib/api/clinician";
import { formatDateTime } from "@/lib/format";

/** Outcome series: fixed order and colours (validated categorical palette in globals.css). */
const OUTCOMES = [
  { key: "correct", label: "Correct", color: "var(--chart-outcome-correct)" },
  { key: "close", label: "Close", color: "var(--chart-outcome-close)" },
  {
    key: "incorrect",
    label: "Incorrect",
    color: "var(--chart-outcome-incorrect)",
  },
  { key: "skipped", label: "Skipped", color: "var(--chart-outcome-skipped)" },
] as const;

const sessionLabel = (i: number) => `#${i + 1}`;

/** Whole numbers as-is; otherwise one decimal (avoids duplicate-looking rounded ticks). */
const formatTick = (v: number) =>
  Number.isInteger(v) ? String(v) : v.toFixed(1);

function ChartCard({
  title,
  description,
  summary,
  table,
  children,
}: {
  title: string;
  description: string;
  summary: string;
  table: ReactNode;
  children: ReactNode;
}) {
  const id = useId();
  return (
    <figure
      aria-labelledby={`${id}-t`}
      className="flex flex-col gap-3 rounded-card border border-line bg-surface p-5"
    >
      <figcaption>
        <p id={`${id}-t`} className="font-bold">
          {title}
        </p>
        <p className="text-sm text-ink-muted">{description}</p>
      </figcaption>
      {/* The animated chart is a visual summary; the same data is in the table below. */}
      <div role="img" aria-label={summary}>
        {children}
      </div>
      <details className="text-sm">
        <summary className="cursor-pointer font-bold text-accent">
          Show data table
        </summary>
        {table}
      </details>
    </figure>
  );
}

export function AnswersBySessionChart({ trend }: { trend: TrendPoint[] }) {
  const data = trend.map((t, i) => ({
    // Numbered, not timed: two sessions can start in the same minute.
    name: sessionLabel(i),
    when: formatDateTime(t.started_at),
    correct: t.correct,
    close: t.near_miss,
    incorrect: t.incorrect,
    skipped: t.skipped,
  }));
  const totals = OUTCOMES.map((o) => ({
    label: o.label,
    color: o.color,
    value: data.reduce((n, d) => n + d[o.key], 0),
  }));
  const answered = totals.reduce((n, t) => n + t.value, 0);

  return (
    <ChartCard
      title="Answers by session"
      description={`Each answer in the last ${trend.length} sessions (#1 is the oldest).`}
      summary={`Stacked bars for ${trend.length} sessions. In total: ${totals
        .map((t) => `${t.value} ${t.label.toLowerCase()}`)
        .join(", ")}.`}
      table={
        <div
          tabIndex={0}
          aria-label="Scrollable table"
          className="mt-3 overflow-x-auto"
        >
          <table className="w-full text-left">
            <caption className="sr-only">Answers by session</caption>
            <thead className="text-ink-muted">
              <tr>
                <th scope="col" className="py-1 pr-3">
                  Session
                </th>
                {OUTCOMES.map((o) => (
                  <th key={o.key} scope="col" className="py-1 pr-3">
                    {o.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-line tabular-nums">
              {trend.map((t, i) => (
                <tr key={t.session_id}>
                  <th scope="row" className="py-1 pr-3 font-normal">
                    {sessionLabel(i)} · {formatDateTime(t.started_at)}
                  </th>
                  <td className="py-1 pr-3">{t.correct}</td>
                  <td className="py-1 pr-3">{t.near_miss}</td>
                  <td className="py-1 pr-3">{t.incorrect}</td>
                  <td className="py-1 pr-3">{t.skipped}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      }
    >
      <BarChart
        data={data}
        xDataKey="name"
        stacked
        stackGap={2}
        aspectRatio="16 / 9"
        margin={{ top: 28, right: 12, bottom: 32, left: 36 }}
      >
        <Grid horizontal />
        {OUTCOMES.map((o) => (
          <Bar key={o.key} dataKey={o.key} fill={o.color} lineCap={4} />
        ))}
        <YAxis numTicks={4} formatValue={formatTick} />
        <BarXAxis maxLabels={6} />
        <ChartTooltip
          rows={(p) => [
            ...OUTCOMES.map((o) => ({
              color: o.color,
              label: o.label,
              value: Number(p[o.key] ?? 0),
            })),
            { color: "transparent", label: "Started", value: String(p.when) },
          ]}
        />
      </BarChart>
      <Legend
        items={totals.map((t) => ({ ...t, maxValue: answered }))}
        className="mt-2 flex flex-row flex-wrap gap-x-2"
      >
        <LegendItem className="flex items-center gap-2 text-sm">
          <LegendMarker />
          <LegendLabel />
          <LegendValue />
        </LegendItem>
      </Legend>
    </ChartCard>
  );
}

export function DifficultyBySessionChart({ trend }: { trend: TrendPoint[] }) {
  // Sessions are evenly spaced (index-based x), so irregular gaps between sessions do not
  // distort the line. The chart's time axis is hidden; session numbers and times are in
  // the tooltip and table.
  const data = trend.map((t, i) => ({
    date: new Date(Date.UTC(2000, 0, 1 + i)),
    session: sessionLabel(i),
    when: formatDateTime(t.started_at),
    difficulty: t.avg_difficulty,
  }));
  const last = trend.at(-1);

  return (
    <ChartCard
      title="Exercise difficulty by session"
      description="Average difficulty (1–5) of the exercises answered, session #1 to the latest."
      summary={`Line chart of average difficulty over ${trend.length} sessions${
        last ? `; most recent ${last.avg_difficulty.toFixed(1)}` : ""
      }.`}
      table={
        <div
          tabIndex={0}
          aria-label="Scrollable table"
          className="mt-3 overflow-x-auto"
        >
          <table className="w-full text-left">
            <caption className="sr-only">
              Exercise difficulty by session
            </caption>
            <thead className="text-ink-muted">
              <tr>
                <th scope="col" className="py-1 pr-3">
                  Session
                </th>
                <th scope="col" className="py-1 pr-3">
                  Average difficulty
                </th>
                <th scope="col" className="py-1">
                  Answers
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line tabular-nums">
              {trend.map((t, i) => (
                <tr key={t.session_id}>
                  <th scope="row" className="py-1 pr-3 font-normal">
                    {sessionLabel(i)} · {formatDateTime(t.started_at)}
                  </th>
                  <td className="py-1 pr-3">{t.avg_difficulty.toFixed(1)}</td>
                  <td className="py-1">{t.attempted}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      }
    >
      <LineChart
        data={data}
        xDataKey="date"
        aspectRatio="16 / 9"
        margin={{ top: 28, right: 24, bottom: 16, left: 36 }}
      >
        <Grid horizontal />
        <Line
          dataKey="difficulty"
          stroke="var(--chart-line-primary)"
          curve={curveMonotoneX}
          showMarkers
        />
        <YAxis numTicks={4} formatValue={formatTick} />
        <ChartTooltip
          showDatePill={false}
          rows={(p) => [
            {
              color: "var(--chart-line-primary)",
              label: `Session ${String(p.session)}`,
              value: Number(p.difficulty).toFixed(1),
            },
            { color: "transparent", label: "Started", value: String(p.when) },
          ]}
        />
      </LineChart>
    </ChartCard>
  );
}
