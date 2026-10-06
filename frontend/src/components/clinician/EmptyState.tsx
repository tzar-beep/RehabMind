import type { LucideIcon } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { buttonClasses } from "@/components/ui/Button";

/** Nothing to show yet: what is missing, why, and (when there is one) the next step. */
export function EmptyState({
  icon: Icon,
  title,
  action,
  children,
}: {
  icon: LucideIcon;
  title: string;
  action?: { href: string; label: string };
  children?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-card border border-dashed border-line-strong bg-surface px-6 py-10 text-center">
      <span
        aria-hidden="true"
        className="grid size-14 place-items-center rounded-full bg-accent-soft text-accent-hover"
      >
        <Icon size={26} />
      </span>
      <p className="text-lg font-bold">{title}</p>
      {children && <div className="max-w-prose text-ink-muted">{children}</div>}
      {action && (
        <Link href={action.href} className={`mt-2 ${buttonClasses("primary")}`}>
          {action.label}
        </Link>
      )}
    </div>
  );
}
