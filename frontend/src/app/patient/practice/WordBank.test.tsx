import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import { feedbackFor, IMAGE_ALT } from "./messages";
import { WordBank } from "./WordBank";

const WORDS = ["dog", "is", "running", "the"];

function setup() {
  const onCheck = vi.fn();
  const onSkip = vi.fn();
  const utils = render(
    <WordBank
      words={WORDS}
      busy={false}
      error={null}
      onCheck={onCheck}
      onSkip={onSkip}
    />,
  );
  return { ...utils, onCheck, onSkip, user: userEvent.setup() };
}

describe("WordBank", () => {
  it("builds the sentence in tap order and submits it", async () => {
    const { user, onCheck } = setup();
    for (const w of ["the", "dog", "is", "running"]) {
      await user.click(screen.getByRole("button", { name: `Add ${w}` }));
    }
    expect(screen.getByText("All words used.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Check" }));
    expect(onCheck).toHaveBeenCalledWith("the dog is running");
  });

  it("removes a placed word when tapped and can clear", async () => {
    const { user, onCheck } = setup();
    await user.click(screen.getByRole("button", { name: "Add dog" }));
    await user.click(screen.getByRole("button", { name: "Add is" }));
    await user.click(screen.getByRole("button", { name: /^dog, word 1/ }));
    expect(screen.getByRole("button", { name: "Add dog" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Clear" }));
    await user.click(screen.getByRole("button", { name: "Check" }));
    expect(onCheck).toHaveBeenCalledWith("");
  });

  it("works with the keyboard and has no axe violations", async () => {
    const { user, container } = setup();
    await user.tab();
    expect(screen.getByRole("button", { name: "Add dog" })).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(
      screen.getByRole("button", { name: /^dog, word 1/ }),
    ).toBeInTheDocument();
    expect((await axe(container)).violations).toEqual([]);
  });
});

describe("feedback copy", () => {
  it("adapts the lead to the exercise type", () => {
    expect(feedbackFor("picture_naming", "incorrect").lead).toBe("The word is");
    expect(feedbackFor("sentence_construction", "incorrect").lead).toBe(
      "The sentence is",
    );
    expect(feedbackFor("picture_description", "correct").lead).toBe(
      "You described it",
    );
  });

  it("never names the picture in alt text", () => {
    for (const alt of Object.values(IMAGE_ALT))
      expect(alt).toMatch(/^Picture /);
  });
});
