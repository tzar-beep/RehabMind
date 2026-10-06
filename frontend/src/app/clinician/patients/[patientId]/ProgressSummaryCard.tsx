"use client";

import { Sparkles, TrendingUp, Target } from "lucide-react";
import { useState } from "react";

import { StatusBadge } from "@/components/clinician/StatusBadge";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { ApiError, apiFetch } from "@/lib/api/client";
import {
  ProgressSummarySchema,
  type AIStatus,
  type ProgressSummary,
} from "@/lib/api/clinician";
import { formatDateTime } from "@/lib/format";

/** GenAI use case 3: an on-request summary of recorded practice, for the clinician only. */
export function ProgressSummaryCard({
  patientId,
  initial,
  status,
}: {
  patientId: string;
  initial: ProgressSummary | null;
  status: AIStatus | null;
}) {
  const [summary, setSummary] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const model = status?.generative ? status.model : null;

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      const r = await apiFetch(
        `/patients/${patientId}/progress-summary`,
        { method: "POST" },
        ProgressSummarySchema,
      );
      setSummary(r ?? null);
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
    <div className="flex flex-col gap-4 rounded-card border border-line bg-surface p-6 shadow-card">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="flex items-center gap-2 text-sm text-ink-muted">
          <Sparkles aria-hidden="true" size={18} className="text-accent" />
          {model
            ? `Written by the local language model ${model}`
            : status?.provider === "fake"
              ? "Offline test provider (not a language model)"
              : "AI is not enabled; a rule-based summary is used"}
        </p>
        <Button variant="secondary" onClick={generate} busy={busy}>
          <Sparkles aria-hidden="true" size={18} />
          {busy
            ? "Writing summary…"
            : summary
              ? "Write a new summary"
              : "Write a progress summary"}
        </Button>
      </div>

      {error && <Alert tone="error">{error}</Alert>}

      {summary ? (
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center gap-2">
            {summary.source === "ai" ? (
              <StatusBadge tone="info">
                AI draft · {summary.prompt_version}
              </StatusBadge>
            ) : (
              <StatusBadge tone="neutral">
                Rule-based summary (AI unavailable)
              </StatusBadge>
            )}
            {summary.created_at && (
              <span className="text-sm text-ink-muted">
                {formatDateTime(summary.created_at)}
                {summary.model && ` · ${summary.model}`}
              </span>
            )}
          </div>
          <p className="text-lg">{summary.summary}</p>
          {(summary.strengths.length > 0 || summary.focus_areas.length > 0) && (
            <div className="grid gap-4 sm:grid-cols-2">
              {summary.strengths.length > 0 && (
                <div className="rounded-control bg-success-soft p-4">
                  <p className="flex items-center gap-2 font-bold text-success">
                    <TrendingUp aria-hidden="true" size={18} />
                    Strengths
                  </p>
                  <ul className="mt-1 list-disc pl-5">
                    {summary.strengths.map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}
              {summary.focus_areas.length > 0 && (
                <div className="rounded-control bg-warning-soft p-4">
                  <p className="flex items-center gap-2 font-bold text-warning">
                    <Target aria-hidden="true" size={18} />
                    Focus areas
                  </p>
                  <ul className="mt-1 list-disc pl-5">
                    {summary.focus_areas.map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
          <p className="text-sm text-ink-muted">
            Draft written from recorded practice figures only. Numbers are
            checked against the data; it is not a clinical assessment.
          </p>
        </div>
      ) : (
        <p className="text-ink-muted">
          No summary yet. It covers word retrieval, sentence formation and
          descriptive language since the latest fresh start.
        </p>
      )}
    </div>
  );
}
