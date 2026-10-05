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

/** Compact facts list (label above value). */
export function Facts({
  items,
}: {
  items: { label: string; value: ReactNode; hint?: string }[];
}) {
  return (
    <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-card border border-line bg-line md:grid-cols-4">
      {items.map((it) => (
        <div
          key={it.label}
          className="flex flex-col gap-1 bg-surface px-5 py-4"
        >
          <dt className="text-sm text-ink-muted">{it.label}</dt>
          <dd className="text-2xl font-bold tabular-nums">{it.value}</dd>
          {it.hint && <dd className="text-sm text-ink-muted">{it.hint}</dd>}
        </div>
      ))}
    </dl>
  );
}
