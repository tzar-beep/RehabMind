import type { Outcome } from "@/lib/api/schemas";

/**
 * Patient-facing feedback. Short, warm, honest: describes the attempt,
 * never makes medical claims, never scolds. The word is always shown with the
 * picture so every attempt ends with the correct pairing.
 */
export const FEEDBACK: Record<Outcome, { title: string; lead: string }> = {
  correct: { title: "Nice work.", lead: "You named it" },
  near_miss: { title: "Very close.", lead: "The word is" },
  incorrect: { title: "Good try.", lead: "The word is" },
  skipped: { title: "That's okay.", lead: "The word is" },
};
