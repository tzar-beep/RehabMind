import type { Metadata } from "next";

import { PracticeSession } from "./PracticeSession";

export const metadata: Metadata = { title: "Practice" };

export default function PracticePage() {
  // One picture, one task: practice keeps a narrow, focused column.
  return (
    <div className="mx-auto w-full max-w-3xl">
      <PracticeSession />
    </div>
  );
}
