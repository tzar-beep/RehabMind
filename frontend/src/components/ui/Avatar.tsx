import { cn } from "@/lib/utils";

// Soft background + strong text pairs; every pair passes WCAG AA for bold text.
const PALETTE = [
  "bg-accent-soft text-accent-hover",
  "bg-[#e5edf9] text-[#2f5ea8]",
  "bg-warning-soft text-warning",
  "bg-[#f1eaf7] text-[#6b4a85]",
  "bg-success-soft text-success",
];

const TITLES = new Set(["dr", "dr.", "mr", "mr.", "mrs", "mrs.", "ms", "ms."]);

export function initials(name: string): string {
  const parts = name
    .split(/\s+/)
    .filter((p) => p && !TITLES.has(p.toLowerCase()));
  const letters =
    parts.length > 1 ? parts[0][0] + parts[parts.length - 1][0] : parts[0]?.[0];
  return (letters ?? "?").toUpperCase();
}

function tone(name: string): string {
  let h = 0;
  for (const ch of name) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return PALETTE[h % PALETTE.length];
}

/** Initials in a soft coloured circle. Decorative: the name is always shown beside it. */
export function Avatar({
  name,
  size = "md",
  className,
}: {
  name: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "grid shrink-0 place-items-center rounded-full font-bold",
        size === "sm" && "size-9 text-sm",
        size === "md" && "size-11 text-base",
        size === "lg" && "size-16 text-2xl",
        tone(name),
        className,
      )}
    >
      {initials(name)}
    </span>
  );
}
