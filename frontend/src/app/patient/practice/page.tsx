import type { Metadata } from "next";

import { PracticeSession } from "./PracticeSession";

export const metadata: Metadata = { title: "Practice" };

export default function PracticePage() {
  return <PracticeSession />;
}
