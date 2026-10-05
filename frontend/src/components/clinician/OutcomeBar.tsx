import type { OutcomeCounts } from "@/lib/api/clinician";

/** Text-first outcome breakdown; counts are always written out, never colour-only. */
export function OutcomeText({ o }: { o: OutcomeCounts }) {
  return (
    <span className="tabular-nums">
      {o.correct} correct · {o.near_miss} close · {o.incorrect} incorrect ·{" "}
      {o.skipped} skipped
    </span>
  );
}
