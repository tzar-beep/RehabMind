"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError, apiFetch } from "@/lib/api/client";
import { SessionStateSchema } from "@/lib/api/schemas";

import { TalkLink } from "./TalkLink";

/**
 * Undo for "Stop for today": for half an hour the patient can carry on from the picture
 * they left, instead of being asked "Are you sure?" when they stop.
 */
export function KeepGoing({
  sessionId,
  answered,
}: {
  sessionId: string;
  answered: number;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function keepGoing() {
    setBusy(true);
    setError(null);
    try {
      await apiFetch(
        `/practice/sessions/${sessionId}/resume`,
        { method: "POST" },
        SessionStateSchema,
      );
      router.push("/patient/practice");
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.message
          : "That didn’t work. Please try again.",
      );
      setBusy(false);
    }
  }

  return (
    <>
      <p className="max-w-md text-xl text-ink-muted">
        You stopped after {answered} {answered === 1 ? "picture" : "pictures"}.
        You can carry on where you left off.
      </p>
      {error && (
        <p role="alert" className="text-lg font-bold text-danger">
          {error}
        </p>
      )}
      <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-3">
        <button
          type="button"
          onClick={keepGoing}
          disabled={busy}
          className="inline-flex min-h-16 w-full items-center justify-center gap-3 rounded-control bg-accent px-8 text-xl font-bold whitespace-nowrap text-white transition-[background-color,transform] hover:bg-accent-hover active:scale-[0.98] disabled:opacity-70 sm:w-fit"
        >
          {busy ? "Opening…" : "Keep going"}
          <ArrowRight aria-hidden="true" size={24} />
        </button>
        <TalkLink />
        <Link
          href="/patient/practice"
          className="inline-flex min-h-target items-center text-lg font-bold underline underline-offset-4"
        >
          Start new practice
        </Link>
      </div>
    </>
  );
}
