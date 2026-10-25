import { Frown, Meh, Smile, type LucideIcon } from "lucide-react";

import type { MoodDay } from "@/lib/api/schemas";

/** The three daily moods, shared by the patient's check-in and the clinician's view. */
export const MOODS: {
  mood: MoodDay["mood"];
  label: string;
  Icon: LucideIcon;
}[] = [
  { mood: "good", label: "Good", Icon: Smile },
  { mood: "okay", label: "Okay", Icon: Meh },
  { mood: "low", label: "Low", Icon: Frown },
];
