import type { Metadata } from "next";

import { PracticeSession } from "./PracticeSession";

export const metadata: Metadata = { title: "Practice" };

export default function PracticePage() {
  // One picture, one task: practice keeps its own focused width.
  return (
    <div className="mx-auto flex min-h-0 w-full max-w-5xl flex-1 flex-col">
      <PracticeSession />
    </div>
  );
}
