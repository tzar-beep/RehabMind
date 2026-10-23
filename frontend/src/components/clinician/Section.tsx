import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

/** Titled content region; headings give screen-reader users a navigable outline. */
export function Section({
  id,
  title,
  description,
  action,
  children,
}: {
  id: string;
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section aria-labelledby={id} className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id={id} className="text-xl font-bold">
            {title}
          </h2>
          {description && (
            <p className="text-base text-ink-muted">{description}</p>
          )}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

// Columns chosen from the item count so no row ends with an orphan cell.
const COLUMNS: Record<number, string> = {
  2: "md:grid-cols-2",
  3: "md:grid-cols-3",
  4: "md:grid-cols-4",
  5: "md:grid-cols-5",
  6: "md:grid-cols-3",
  8: "md:grid-cols-4",
  9: "md:grid-cols-3",
  10: "md:grid-cols-5",
};

/**
 * Headline figures as one container split by 1px dividers (label above value). Figures are
 * type, not tiles: no icons. `icon` is accepted for compatibility and not drawn.
 */
export function Facts({
  items,
}: {
  items: {
    label: string;
    value: ReactNode;
    hint?: string;
    icon?: LucideIcon;
  }[];
}) {
  return (
    <dl
      className={`grid grid-cols-2 gap-px overflow-hidden rounded-card border border-line bg-line ${
        COLUMNS[items.length] ?? "md:grid-cols-4"
      }`}
    >
      {items.map(({ label, value, hint }, i) => (
        <div
          key={label}
          className={`flex flex-col gap-1 bg-surface p-5 ${
            items.length % 2 === 1 && i === items.length - 1
              ? "col-span-2 md:col-span-1"
              : ""
          } ${items.length > 4 ? "md:p-4" : ""}`}
        >
          <dt className="text-sm text-ink-muted">{label}</dt>
          <dd className="text-2xl font-bold tabular-nums">{value}</dd>
          {hint && <dd className="text-sm text-ink-muted">{hint}</dd>}
        </div>
      ))}
    </dl>
  );
}
