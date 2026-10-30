import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { WeekActivity } from "./WeekActivity";

vi.mock("@/components/CountUp", () => ({ CountUp: () => null }));
vi.mock("./PracticeCalendar", async (importActual) => ({
  ...(await importActual<typeof import("./PracticeCalendar")>()),
  PracticeCalendar: () => null,
}));

const activity = (...days: string[]) => ({
  sessions_completed: days.length,
  pictures_practised: days.length,
  recent: days.map((d) => ({ started_at: `${d}T12:00:00`, answered: 1 })),
});

describe("WeekActivity", () => {
  beforeEach(() => {
    vi.useFakeTimers({ now: new Date(2026, 9, 30, 12), toFake: ["Date"] }); // a Friday
  });
  afterEach(() => vi.useRealTimers());

  it("counts this week from Monday, the same week as the goals", () => {
    render(<WeekActivity activity={activity("2026-10-25", "2026-10-26", "2026-10-28")} />);
    screen.getByText("You practised on 2 days this week.");
  });

  it("does not count last weekend as this week", () => {
    render(<WeekActivity activity={activity("2026-10-24", "2026-10-25")} />);
    expect(screen.queryByText(/this week/)).toBeNull();
    screen.getByText("Every day is a fresh start.");
  });

  it("says when the patient practised today", () => {
    render(<WeekActivity activity={activity("2026-10-30")} />);
    screen.getByText("You practised today. Well done.");
  });
});
