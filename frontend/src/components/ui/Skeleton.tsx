import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

/** A calm placeholder block while content loads (still when reduced motion is on). */
export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "animate-pulse rounded-control bg-line/70 motion-reduce:animate-none",
        className,
      )}
    />
  );
}

/** Wraps skeletons with one polite status message for screen readers. */
export function LoadingRegion({
  label,
  className,
  children,
}: {
  label: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <div role="status" className={cn("flex flex-col gap-6", className)}>
      <span className="sr-only">{label}</span>
      {children}
    </div>
  );
}
