import type { Outcome } from "@/lib/api/schemas";

/**
 * Patient-facing feedback. Short, warm, honest: describes the attempt,
 * never makes medical claims, never scolds. The answer is always shown with the
 * picture so every attempt ends with the correct pairing.
 */
const TITLES: Record<Outcome, string> = {
  correct: "Nice work.",
  near_miss: "Very close.",
  incorrect: "Good try.",
  skipped: "That's okay.",
};

const LEADS: Record<string, { correct: string; other: string }> = {
  picture_naming: { correct: "You named it", other: "The word is" },
  picture_description: { correct: "You described it", other: "For example" },
  sentence_construction: { correct: "You built it", other: "The sentence is" },
};

export function feedbackFor(exerciseType: string, outcome: Outcome) {
  const lead = LEADS[exerciseType] ?? LEADS.picture_naming;
  return {
    title: TITLES[outcome],
    lead: outcome === "correct" ? lead.correct : lead.other,
  };
}

/** Alt text must never name the object or scene: that would give the answer away. */
export const IMAGE_ALT: Record<string, string> = {
  picture_naming: "Picture to name",
  picture_description: "Picture to describe",
  sentence_construction: "Picture for the sentence",
};

export const TYPE_HINT: Record<string, string> = {
  picture_naming: "Type the word for this picture.",
  picture_description: "Type a few words about the picture.",
};

export const EMPTY_ANSWER: Record<string, string> = {
  picture_naming: "Type a word, or choose “I’m not sure”.",
  picture_description: "Type a few words, or choose “I’m not sure”.",
  sentence_construction:
    "Tap the words to build a sentence, or choose “I’m not sure”.",
};
