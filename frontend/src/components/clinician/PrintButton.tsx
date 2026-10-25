"use client";

import { Printer } from "lucide-react";

/** Prints the current patient page for case notes (print styles hide navigation). */
export function PrintButton() {
  return (
    <button
      type="button"
      onClick={() => window.print()}
      className="no-print inline-flex min-h-target items-center gap-2 rounded-control border-2 border-line px-4 font-bold text-ink-muted transition-colors hover:border-accent hover:text-ink"
    >
      <Printer aria-hidden="true" size={18} />
      Print
    </button>
  );
}
