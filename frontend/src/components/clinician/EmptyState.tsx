import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

export function EmptyState({
  icon: Icon,
  title,
  children,
}: {
  icon: LucideIcon;
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong bg-surface px-6 py-10 text-center">
      <Icon aria-hidden="true" size={28} className="text-ink-muted" />
      <p className="text-lg font-bold">{title}</p>
      {children && <div className="max-w-prose text-ink-muted">{children}</div>}
    </div>
  );
}
