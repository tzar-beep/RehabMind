"use client";

import { RotateCcw, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useId, useRef, useState, type FormEvent } from "react";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { ApiError, apiFetch } from "@/lib/api/client";
import { ResetInfoSchema } from "@/lib/api/clinician";

/**
 * "Fresh start" for one patient, behind a confirmation dialog with a required reason.
 * Nothing is deleted; the backend records who reset, when and why.
 */
export function ResetProgress({
  patientId,
  patientName,
}: {
  patientId: string;
  patientName: string;
}) {
  const router = useRouter();
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const reasonId = useId();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  function open() {
    setError(null);
    setDone(false);
    dialog.current?.showModal();
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const reason = String(new FormData(form).get("reason") ?? "").trim();
    if (reason.length < 3) {
      setError("Please give a short reason (at least 3 characters).");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await apiFetch(
        `/patients/${patientId}/progress-resets`,
        { method: "POST", json: { reason } },
        ResetInfoSchema,
      );
      form.reset();
      dialog.current?.close();
      setDone(true);
      router.refresh();
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.message
          : "Something went wrong. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {done && (
        <Alert tone="success">
          Progress reset. {patientName}&rsquo;s summaries now start from today.
          Earlier sessions are still in the session history.
        </Alert>
      )}
      <div>
        <Button variant="secondary" onClick={open}>
          <RotateCcw aria-hidden="true" size={18} />
          Reset progress…
        </Button>
      </div>

      <dialog
        ref={dialog}
        aria-labelledby={titleId}
        className="m-auto w-[min(36rem,calc(100%-2rem))] rounded-card border border-line bg-surface p-0 text-ink shadow-2xl backdrop:bg-ink/50 backdrop:backdrop-blur-sm"
      >
        <form
          onSubmit={onSubmit}
          noValidate
          className="flex flex-col gap-5 p-8"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-3">
              <span
                aria-hidden="true"
                className="grid size-12 shrink-0 place-items-center rounded-full bg-warning-soft text-warning"
              >
                <RotateCcw size={24} />
              </span>
              <h2 id={titleId} className="text-2xl font-bold">
                Give {patientName} a fresh start?
              </h2>
            </div>
            <button
              type="button"
              onClick={() => dialog.current?.close()}
              aria-label="Close"
              className="grid size-11 shrink-0 place-items-center rounded-control text-ink-muted hover:bg-canvas hover:text-ink"
            >
              <X aria-hidden="true" size={22} />
            </button>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-control bg-canvas p-4">
              <p className="font-bold">What changes</p>
              <ul className="mt-1 list-disc pl-5 text-ink-muted">
                <li>
                  Summaries, trends and the patient&rsquo;s week start at zero
                </li>
                <li>Difficulty restarts at the lowest level you allow</li>
                <li>Any open session is closed</li>
              </ul>
            </div>
            <div className="rounded-control bg-canvas p-4">
              <p className="font-bold">What is kept</p>
              <ul className="mt-1 list-disc pl-5 text-ink-muted">
                <li>
                  Every past session and answer, marked &ldquo;Before fresh
                  start&rdquo;
                </li>
                <li>The AI audit log and practice limits</li>
                <li>A record of who reset, when and why</li>
              </ul>
            </div>
          </div>

          {error && <Alert tone="error">{error}</Alert>}

          <div className="flex flex-col gap-1.5">
            <label htmlFor={reasonId} className="font-bold">
              Reason (required)
            </label>
            <textarea
              id={reasonId}
              name="reason"
              required
              maxLength={500}
              rows={3}
              placeholder="For example: starting a new therapy block"
              className="rounded-control border-2 border-line-strong bg-surface px-4 py-3 text-lg"
            />
          </div>

          <div className="flex flex-wrap justify-end gap-3">
            <Button variant="secondary" onClick={() => dialog.current?.close()}>
              Cancel
            </Button>
            <Button type="submit" busy={busy}>
              Reset progress
            </Button>
          </div>
        </form>
      </dialog>
    </div>
  );
}
