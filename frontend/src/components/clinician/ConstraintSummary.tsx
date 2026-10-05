import type { ConstraintFields } from "@/lib/api/clinician";
import { exerciseType, responseMode } from "@/lib/format";

export function constraintRows(
  c: ConstraintFields,
): { label: string; value: string }[] {
  return [
    {
      label: "Exercise types",
      value: c.allowed_exercise_types.map(exerciseType).join(", "),
    },
    {
      label: "Answer methods",
      value: c.allowed_response_modes.map(responseMode).join(", "),
    },
    {
      label: "Picture categories",
      value: c.allowed_categories?.length
        ? c.allowed_categories.join(", ")
        : "All categories",
    },
    {
      label: "Difficulty range",
      value: `${c.min_difficulty} to ${c.max_difficulty} (of 5)`,
    },
    {
      label: "Exercises per session",
      value: String(c.max_exercises_per_session),
    },
    {
      label: "Increase difficulty after",
      value: `${c.advance_after_correct} correct in a row`,
    },
    {
      label: "Decrease difficulty after",
      value: `${c.step_back_after_incorrect} incorrect or skipped in a row`,
    },
  ];
}

export function ConstraintSummary({
  constraints,
}: {
  constraints: ConstraintFields;
}) {
  return (
    <dl className="grid gap-x-8 gap-y-3 sm:grid-cols-2">
      {constraintRows(constraints).map((r) => (
        <div key={r.label} className="flex flex-col">
          <dt className="text-sm text-ink-muted">{r.label}</dt>
          <dd className="font-bold">{r.value}</dd>
        </div>
      ))}
    </dl>
  );
}
