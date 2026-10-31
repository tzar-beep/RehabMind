import { cn } from "@/lib/utils";

/**
 * RehabMind logo mark: an R with a break in its stem, where one dot holds the gap like
 * a word coming back, on a teal tile. Decorative; the wordmark carries the name.
 * Masters and usage rules are in brand/logo/.
 */
export function BrandLogo({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 256 256"
      aria-hidden="true"
      focusable="false"
      className={cn("size-9 shrink-0", className)}
    >
      <rect width="256" height="256" rx="70" fill="#0f6e6e" />
      <g transform="translate(32.47 33.92) scale(0.735)">
        <path
          d="M65 20H141A72 72 0 0 1 168.92 158.36L198.16 209A18 18 0 0 1 166.98 227L130.61 164H83V218A18 18 0 0 1 47 218V146A18 18 0 0 1 65 128H141A36 36 0 0 0 141 56H65A18 18 0 0 1 65 20Z"
          fill="#ffffff"
        />
        <circle cx="65" cy="92" r="16" fill="#f4b860" />
      </g>
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
      <BrandLogo className={cn(large && "size-12")} />
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
