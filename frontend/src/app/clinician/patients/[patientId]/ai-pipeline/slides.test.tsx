import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { PipelineGeneration } from "@/lib/api/clinician";

import { PromptVisual } from "./slides";

const USER_PROMPT = `REHABILITATION OBJECTIVE: Improve word retrieval
CANDIDATE STIMULI (choose exactly one): []

TASK: Generate ONE picture_naming exercise for this patient.

EXAMPLE (a different picture; do not copy its words):
If the candidate were {"slug": "example_cup"}:
GOOD: {"semantic_cue": "You pour tea or coffee in it."}
BAD: "semantic_cue": "A cup holds your tea." (it uses an avoid word)

CHECK before answering: no avoid word appears.

OUTPUT: one JSON object.`;

describe("PromptVisual", () => {
  it("labels each prompt-engineering technique", () => {
    render(
      <PromptVisual
        gen={
          {
            prompt_version: "exercise_generation_v2",
            user_prompt: USER_PROMPT,
          } as PipelineGeneration
        }
      />,
    );
    for (const label of ["Objective", "Constraint", "Task", "Self-check", "Format"]) {
      screen.getByText(label);
    }
    expect(screen.getAllByText("Few-shot")).toHaveLength(4);
  });
});
