import { describe, expect, it } from "vitest";

import type { ConstraintFields, ConstraintOptions } from "@/lib/api/clinician";

import {
  changedKeys,
  picturesAvailable,
  validateConstraints,
} from "./constraints";

const opts: ConstraintOptions = {
  exercise_types: [
    { value: "picture_naming", available: true },
    { value: "sentence_completion", available: false },
  ],
  response_modes: ["text", "speech"],
  categories: { animals: { "1": 3, "2": 2 }, tools: { "4": 2, "5": 3 } },
  difficulty: [1, 5],
  max_exercises_per_session: [1, 50],
  progression_rule: [1, 10],
};

const valid: ConstraintFields = {
  allowed_exercise_types: ["picture_naming"],
  allowed_response_modes: ["text"],
  allowed_categories: null,
  min_difficulty: 1,
  max_difficulty: 3,
  max_exercises_per_session: 8,
  advance_after_correct: 3,
  step_back_after_incorrect: 2,
  note: null,
};

describe("validateConstraints", () => {
  it("accepts a valid configuration", () => {
    expect(validateConstraints(valid, opts)).toEqual({});
  });

  it.each([
    [{ min_difficulty: 4, max_difficulty: 2 }, "max_difficulty"],
    [{ max_difficulty: 6 }, "max_difficulty"],
    [{ allowed_exercise_types: [] }, "allowed_exercise_types"],
    [
      { allowed_exercise_types: ["sentence_completion"] },
      "allowed_exercise_types",
    ],
    [{ allowed_response_modes: [] }, "allowed_response_modes"],
    [{ allowed_categories: [] }, "allowed_categories"],
    [{ max_exercises_per_session: 51 }, "max_exercises_per_session"],
    [{ max_exercises_per_session: Number.NaN }, "max_exercises_per_session"],
    [{ advance_after_correct: 0 }, "advance_after_correct"],
    [{ step_back_after_incorrect: 2.5 }, "step_back_after_incorrect"],
  ])("rejects %j", (patch, field) => {
    const v = { ...valid, ...patch } as ConstraintFields;
    expect(validateConstraints(v, opts)).toHaveProperty(field);
  });
});

describe("picturesAvailable", () => {
  it("counts pictures inside the categories and difficulty range", () => {
    expect(picturesAvailable(valid, opts)).toBe(5);
    expect(
      picturesAvailable({ ...valid, allowed_categories: ["tools"] }, opts),
    ).toBe(0);
  });
});

describe("changedKeys", () => {
  it("ignores the note and list order", () => {
    expect(changedKeys(valid, { ...valid, note: "x" })).toEqual([]);
    expect(changedKeys(valid, { ...valid, max_difficulty: 2 })).toEqual([
      "max_difficulty",
    ]);
  });
});
