import { CircleCheck, Target } from "lucide-react";

import type { Goal } from "@/lib/api/schemas";

/**
 * The patient's goals, in the words their clinician chose, with progress from their own
 * practice. Progress only: nothing here says what went wrong.
 */
export function PatientGoals({ goals }: { goals: Goal[] }) {
  return (
    <section
      aria-labelledby="goals-heading"
      className="flex w-full flex-col gap-3 rounded-card bg-white/8 p-5 md:w-[22rem]"
    >
      <h2
        id="goals-heading"
        className="flex items-center gap-2 text-lg font-bold"
      >
        <Target aria-hidden="true" size={20} />
        Your goals
      </h2>
      <ul className="flex flex-col gap-4">
        {goals.map((g) => {
          const reached = g.status === "achieved";
          const share = Math.min(g.progress / g.target, 1);
          return (
            <li key={g.id} className="flex flex-col gap-1.5">
              <span className="flex items-start gap-2 text-base font-bold">
                {reached && (
                  <CircleCheck
                    aria-hidden="true"
                    size={20}
                    className="mt-0.5 shrink-0 text-brand-glow"
                  />
                )}
                {g.title}
              </span>
              <span className="flex items-center gap-3">
                <span
                  aria-hidden="true"
                  className="h-2.5 flex-1 overflow-hidden rounded-full bg-white/15"
                >
                  <span
                    className="block h-full rounded-full bg-brand-glow"
                    style={{ width: `${share * 100}%` }}
                  />
                </span>
                <span className="text-sm text-brand-muted tabular-nums">
                  {reached ? "Reached!" : `${g.progress} of ${g.target}`}
                </span>
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
