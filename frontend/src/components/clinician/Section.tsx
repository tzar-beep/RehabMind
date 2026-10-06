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

/** Stat tiles (label above value), each with an optional icon chip. */
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
    <dl className="grid grid-cols-1 gap-4 min-[420px]:grid-cols-2 md:grid-cols-4">
      {items.map(({ label, value, hint, icon: Icon }) => (
        <div
          key={label}
          className="flex flex-col gap-1 rounded-card border border-line bg-surface p-5 shadow-card"
        >
          <dt className="flex items-center gap-2.5 text-sm font-bold text-ink-muted">
            {Icon && (
              <span
                aria-hidden="true"
                className="grid size-8 shrink-0 place-items-center rounded-lg bg-accent-soft text-accent-hover"
              >
                <Icon size={17} />
              </span>
            )}
            {label}
          </dt>
          <dd className="mt-1 text-3xl font-bold tabular-nums">{value}</dd>
          {hint && <dd className="text-sm text-ink-muted">{hint}</dd>}
        </div>
      ))}
    </dl>
  );
}
