import { Speech } from "lucide-react";

import { cn } from "@/lib/utils";

/** RehabMind logo: icon tile plus wordmark. `inverted` is for dark backgrounds. */
export function BrandMark({
  inverted = false,
  className,
}: {
  inverted?: boolean;
  className?: string;
}) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <span
        aria-hidden="true"
        className={cn(
          "grid size-9 place-items-center rounded-xl shadow-sm",
          inverted
            ? "bg-white/15 text-white ring-1 ring-white/25"
            : "bg-linear-to-br from-accent to-brand-deep text-white",
        )}
      >
        <Speech className="size-5" strokeWidth={2.25} />
      </span>
      <span className="text-lg font-bold tracking-tight">RehabMind</span>
    </span>
  );
}
