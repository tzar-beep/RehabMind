import {
  CircleAlert,
  CircleCheck,
  CircleMinus,
  Info,
  type LucideIcon,
} from "lucide-react";
import type { ReactNode } from "react";

type Tone = "success" | "warning" | "neutral" | "info";

const tones: Record<Tone, { cls: string; Icon: LucideIcon }> = {
  success: { cls: "bg-success-soft text-success", Icon: CircleCheck },
  warning: { cls: "bg-warning-soft text-warning", Icon: CircleAlert },
  neutral: {
    cls: "bg-canvas text-ink-muted border border-line",
    Icon: CircleMinus,
  },
  info: { cls: "bg-accent-soft text-accent-hover", Icon: Info },
};

/** Status is always icon + text, never colour alone. */
export function StatusBadge({
  tone,
  children,
}: {
  tone: Tone;
  children: ReactNode;
}) {
  const { cls, Icon } = tones[tone];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-bold ${cls}`}
    >
      <Icon aria-hidden="true" size={16} strokeWidth={2.25} />
      {children}
    </span>
  );
}
