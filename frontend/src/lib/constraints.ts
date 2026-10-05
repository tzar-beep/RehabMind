import type { ConstraintFields, ConstraintOptions } from "@/lib/api/clinician";

/**
 * Form-level checks for a new constraint version. UX only: the backend validates the
 * same rules (Pydantic + DB CHECK constraints) and is the authority. Limits come from
 * the backend's /clinical/constraint-options, not hard-coded here.
 */
export type ConstraintErrors = Partial<Record<keyof ConstraintFields, string>>;

const inRange = (v: number, [lo, hi]: [number, number]) =>
  Number.isInteger(v) && v >= lo && v <= hi;

export function validateConstraints(
  v: ConstraintFields,
  opts: ConstraintOptions,
): ConstraintErrors {
  const e: ConstraintErrors = {};
  const available = new Set(
    opts.exercise_types.filter((t) => t.available).map((t) => t.value),
  );
  if (!v.allowed_exercise_types.length)
    e.allowed_exercise_types = "Choose at least one exercise type.";
  else if (!v.allowed_exercise_types.some((t) => available.has(t)))
    e.allowed_exercise_types =
      "Include at least one exercise type that is currently available.";
  if (!v.allowed_response_modes.length)
    e.allowed_response_modes = "Choose at least one answer method.";
  if (v.allowed_categories !== null && !v.allowed_categories.length)
    e.allowed_categories =
      "Choose at least one category, or allow all categories.";
  if (!inRange(v.min_difficulty, opts.difficulty))
    e.min_difficulty = "Choose a level from 1 to 5.";
  if (!inRange(v.max_difficulty, opts.difficulty))
    e.max_difficulty = "Choose a level from 1 to 5.";
  else if (v.min_difficulty > v.max_difficulty)
    e.max_difficulty = "Maximum difficulty must be at least the minimum.";
  const [sLo, sHi] = opts.max_exercises_per_session;
  if (!inRange(v.max_exercises_per_session, opts.max_exercises_per_session))
    e.max_exercises_per_session = `Enter a whole number from ${sLo} to ${sHi}.`;
  const [rLo, rHi] = opts.progression_rule;
  if (!inRange(v.advance_after_correct, opts.progression_rule))
    e.advance_after_correct = `Enter a whole number from ${rLo} to ${rHi}.`;
  if (!inRange(v.step_back_after_incorrect, opts.progression_rule))
    e.step_back_after_incorrect = `Enter a whole number from ${rLo} to ${rHi}.`;
  if ((v.note ?? "").length > 500)
    e.note = "Keep the note under 500 characters.";
  return e;
}

/** Pictures in the library that these limits allow (0 means the patient would get none). */
export function picturesAvailable(
  v: ConstraintFields,
  opts: ConstraintOptions,
): number {
  let n = 0;
  for (const [category, levels] of Object.entries(opts.categories)) {
    if (v.allowed_categories && !v.allowed_categories.includes(category))
      continue;
    for (const [level, count] of Object.entries(levels)) {
      const d = Number(level);
      if (d >= v.min_difficulty && d <= v.max_difficulty) n += count;
    }
  }
  return n;
}

const LIMIT_KEYS: (keyof ConstraintFields)[] = [
  "allowed_exercise_types",
  "allowed_response_modes",
  "allowed_categories",
  "min_difficulty",
  "max_difficulty",
  "max_exercises_per_session",
  "advance_after_correct",
  "step_back_after_incorrect",
];

const norm = (x: unknown) =>
  JSON.stringify(Array.isArray(x) ? [...x].sort() : x);

export function changedKeys(
  a: ConstraintFields,
  b: ConstraintFields,
): (keyof ConstraintFields)[] {
  return LIMIT_KEYS.filter((k) => norm(a[k]) !== norm(b[k]));
}
