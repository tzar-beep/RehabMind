import { useId } from "react";

import { cn } from "@/lib/utils";

/**
 * RehabMind logo mark: a speech bubble (language) holding three rising bars (steady
 * progress), on a deep-teal tile. Decorative; the wordmark carries the name.
 */
export function BrandLogo({ className }: { className?: string }) {
  const gradient = useId();
  return (
    <svg
      viewBox="0 0 40 40"
      aria-hidden="true"
      focusable="false"
      className={cn("size-9 shrink-0", className)}
    >
      <defs>
        <linearGradient id={gradient} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#14857f" />
          <stop offset="1" stopColor="#0a3d3e" />
        </linearGradient>
      </defs>
      <rect width="40" height="40" rx="11" fill={`url(#${gradient})`} />
      <path
        d="M13 9h14a5 5 0 0 1 5 5v7a5 5 0 0 1-5 5H18l-5.5 4.5V26H13a5 5 0 0 1-5-5v-7a5 5 0 0 1 5-5Z"
        fill="#ffffff"
      />
      <rect x="13.5" y="18" width="3" height="4" rx="1.5" fill="#0f6e6e" />
      <rect x="18.5" y="15.5" width="3" height="6.5" rx="1.5" fill="#0f6e6e" />
      <rect x="23.5" y="13" width="3" height="9" rx="1.5" fill="#5ec4b6" />
    </svg>
  );
}

/** Logo mark plus two-tone wordmark. `inverted` is for dark backgrounds. */
export function BrandMark({
  inverted = false,
  large = false,
  className,
}: {
  inverted?: boolean;
  large?: boolean;
  className?: string;
}) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <BrandLogo
        className={cn(
          large && "size-12",
          inverted && "rounded-[11px] ring-1 ring-white/25",
        )}
      />
      <span
        className={cn(
          "leading-none font-bold tracking-tight",
          large ? "text-2xl" : "text-xl",
        )}
      >
        <span className={inverted ? "text-white" : "text-ink"}>Rehab</span>
        <span className={inverted ? "text-brand-glow" : "text-accent"}>
          Mind
        </span>
      </span>
    </span>
  );
}
