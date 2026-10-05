import { useId } from "react";

export interface ChartPoint {
  label: string; // x-axis label (e.g. session date)
  value: number;
  detail: string; // full sentence for tooltip and data table
}

/**
 * Single-series line chart: 2px line, ≥8px markers with a surface ring, hairline
 * gridlines, one axis. Every point has a native tooltip, and the same data is always
 * available as a table (screen readers, print, precise reading).
 */
export function LineChart({
  title,
  description,
  points,
  yMin,
  yMax,
  yTicks,
  formatY,
  valueHeader,
}: {
  title: string;
  description: string;
  points: ChartPoint[];
  yMin: number;
  yMax: number;
  yTicks: number[];
  formatY: (v: number) => string;
  valueHeader: string;
}) {
  const id = useId();
  const W = 640;
  const H = 240;
  const pad = { top: 16, right: 20, bottom: 36, left: 48 };
  const iw = W - pad.left - pad.right;
  const ih = H - pad.top - pad.bottom;
  const x = (i: number) =>
    pad.left + (points.length === 1 ? iw / 2 : (i / (points.length - 1)) * iw);
  const y = (v: number) => pad.top + ih - ((v - yMin) / (yMax - yMin)) * ih;
  const path = points
    .map((p, i) => `${i ? "L" : "M"}${x(i)},${y(p.value)}`)
    .join(" ");
  const labelEvery = Math.ceil(points.length / 6);
  const last = points.at(-1);

  return (
    <figure className="flex flex-col gap-3 rounded-card border border-line bg-surface p-5">
      <figcaption>
        <p id={`${id}-t`} className="font-bold">
          {title}
        </p>
        <p id={`${id}-d`} className="text-sm text-ink-muted">
          {description}
        </p>
      </figcaption>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-labelledby={`${id}-t ${id}-d`}
        className="h-auto w-full"
      >
        {yTicks.map((t) => (
          <g key={t}>
            <line
              x1={pad.left}
              x2={W - pad.right}
              y1={y(t)}
              y2={y(t)}
              stroke="var(--color-grid)"
              strokeWidth={1}
            />
            <text
              x={pad.left - 8}
              y={y(t)}
              dy="0.32em"
              textAnchor="end"
              fontSize={12}
              fill="var(--color-ink-muted)"
            >
              {formatY(t)}
            </text>
          </g>
        ))}
        {points.map((p, i) =>
          i % labelEvery === 0 || i === points.length - 1 ? (
            <text
              key={i}
              x={x(i)}
              y={H - 12}
              textAnchor={
                i === 0 ? "start" : i === points.length - 1 ? "end" : "middle"
              }
              fontSize={12}
              fill="var(--color-ink-muted)"
            >
              {p.label}
            </text>
          ) : null,
        )}
        <path
          d={path}
          fill="none"
          stroke="var(--color-chart)"
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {points.map((p, i) => (
          <g key={i}>
            <circle
              cx={x(i)}
              cy={y(p.value)}
              r={5}
              fill="var(--color-chart)"
              stroke="var(--color-surface)"
              strokeWidth={2}
            />
            {/* Larger invisible hit target for the tooltip. */}
            <circle cx={x(i)} cy={y(p.value)} r={14} fill="transparent">
              <title>{p.detail}</title>
            </circle>
          </g>
        ))}
        {last && (
          <text
            x={x(points.length - 1)}
            y={y(last.value) - 12}
            textAnchor="end"
            fontSize={12}
            fontWeight={700}
            fill="var(--color-ink)"
          >
            {formatY(last.value)}
          </text>
        )}
      </svg>
      <details className="text-sm">
        <summary className="cursor-pointer font-bold text-accent">
          Show data table
        </summary>
        <table className="mt-3 w-full text-left">
          <caption className="sr-only">{title}</caption>
          <thead className="text-ink-muted">
            <tr>
              <th scope="col" className="py-1 pr-4">
                Session
              </th>
              <th scope="col" className="py-1 pr-4">
                {valueHeader}
              </th>
              <th scope="col" className="py-1">
                Detail
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {points.map((p, i) => (
              <tr key={i}>
                <td className="py-1 pr-4">{p.label}</td>
                <td className="py-1 pr-4 tabular-nums">{formatY(p.value)}</td>
                <td className="py-1">{p.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}
