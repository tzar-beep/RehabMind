import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ChoiceGrid } from "./Choices";

const OPTIONS = [
  { word: "dog", image_url: "/a.jpg" },
  { word: "cup", image_url: "/b.jpg" },
  { word: "car", image_url: "/c.jpg" },
  { word: "tree", image_url: "/d.jpg" },
];

describe("ChoiceGrid", () => {
  it("never names a picture, so the alt text cannot give the answer away", () => {
    render(<ChoiceGrid options={OPTIONS} busy={false} onPick={() => {}} />);
    const alts = screen.getAllByRole("img").map((i) => i.getAttribute("alt"));
    expect(alts).toEqual([
      "Picture 1 of 4",
      "Picture 2 of 4",
      "Picture 3 of 4",
      "Picture 4 of 4",
    ]);
    for (const { word } of OPTIONS) expect(screen.queryByText(word)).toBeNull();
  });

  it("answers with the tapped picture's word, and not while busy", () => {
    const onPick = vi.fn();
    const { rerender } = render(
      <ChoiceGrid options={OPTIONS} busy={false} onPick={onPick} />,
    );
    fireEvent.click(screen.getAllByRole("button")[2]);
    expect(onPick).toHaveBeenCalledWith("car");
    rerender(<ChoiceGrid options={OPTIONS} busy onPick={onPick} />);
    expect(screen.getAllByRole("button")[0]).toBeDisabled();
  });
});
