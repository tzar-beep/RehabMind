import type { Metadata } from "next";

import { PracticeSession } from "./PracticeSession";

export const metadata: Metadata = { title: "Practice" };

export default function PracticePage() {
  // One picture, one task: practice keeps its own focused width.
  return (
    <div className="mx-auto w-full max-w-5xl">
      <PracticeSession />
    </div>
  );
}
