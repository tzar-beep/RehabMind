import type { ReactNode } from "react";

/**
 * The teal strip across the top of a printed label (the wristband system; see DESIGN.md).
 * For a screen's main panel only: most cards are plain labels. The parent clips the corners.
 */
export function LabelStrip({
  children,
  aside,
}: {
  children: ReactNode;
  aside?: ReactNode;
}) {
  return (
    <p className="flex shrink-0 items-center justify-between gap-4 bg-accent px-[clamp(1.25rem,2.5vw,2rem)] py-2 text-sm font-bold text-white">
      <span>{children}</span>
      {aside && (
        <span className="hidden text-[#cfeee8] sm:inline">{aside}</span>
      )}
    </p>
  );
}
