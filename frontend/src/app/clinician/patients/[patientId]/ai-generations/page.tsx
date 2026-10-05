import { ShieldCheck } from "lucide-react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { z } from "zod";

import { EmptyState } from "@/components/clinician/EmptyState";
import { StatusBadge } from "@/components/clinician/StatusBadge";
import { AIRunSchema, type AIRun } from "@/lib/api/clinician";
import { backendGet } from "@/lib/api/server";
import {
  formatDateTime,
  formatMs,
  outcome,
  reasonLabel,
  SELECTION_REASON,
  SOURCE,
  STAGE,
} from "@/lib/format";

export const metadata: Metadata = { title: "AI audit log" };

const RESULT: Record<
  AIRun["result"],
  { tone: "success" | "info" | "neutral"; label: string; summary: string }
> = {
  ai_generated: {
    tone: "success",
    label: "AI suggestion accepted",
    summary: "The AI suggestion passed all checks on the first attempt.",
  },
  ai_generated_after_retry: {
    tone: "info",
    label: "Accepted after retry",
    summary:
      "The first suggestion was rejected by validation; a retry passed all checks.",
  },
  rule_based_used: {
    tone: "neutral",
    label: "Rule-based exercise used",
    summary:
      "AI suggestions were rejected by validation; a rule-based exercise was used instead.",
  },
  no_exercise: {
    tone: "neutral",
    label: "No exercise issued",
    summary:
      "No AI suggestion was used and no exercise was issued for this slot.",
  },
};

function Run({ run }: { run: AIRun }) {
  const r = RESULT[run.result];
  return (
    <li className="rounded-card border border-line bg-surface">
      <details>
        <summary className="flex min-h-target cursor-pointer flex-wrap items-center gap-x-4 gap-y-2 px-5 py-4">
          <StatusBadge tone={r.tone}>{r.label}</StatusBadge>
          <span className="font-bold">
            {run.position ? `Exercise ${run.position}` : "Exercise"}
            {run.final_exercise?.picture && ` · ${run.final_exercise.picture}`}
          </span>
          <span className="text-sm text-ink-muted">
            {formatDateTime(run.created_at)} · {run.attempts.length}{" "}
            {run.attempts.length === 1 ? "attempt" : "attempts"}
          </span>
        </summary>
        <div className="flex flex-col gap-5 border-t border-line px-5 py-4">
          <p>{r.summary}</p>

          <dl className="grid gap-x-8 gap-y-2 text-sm sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <dt className="text-ink-muted">Patient received</dt>
              <dd className="font-bold">
                {run.final_exercise
                  ? `${SOURCE[run.final_exercise.source] ?? run.final_exercise.source}: ${run.final_exercise.picture ?? "—"}, difficulty ${run.final_exercise.difficulty}, “${run.final_exercise.prompt}”`
                  : "Nothing"}
              </dd>
            </div>
            <div>
              <dt className="text-ink-muted">Selection reason code</dt>
              <dd className="font-bold">
                {run.selection_reason
                  ? (SELECTION_REASON[run.selection_reason] ??
                    run.selection_reason)
                  : "— (no accepted AI output)"}
              </dd>
            </div>
            <div>
              <dt className="text-ink-muted">Practice limits applied</dt>
              <dd className="font-bold">Version {run.constraint_version}</dd>
            </div>
            <div>
              <dt className="text-ink-muted">Input given to the AI</dt>
              <dd>
                Target difficulty {run.target_difficulty}, {run.candidates}{" "}
                allowed pictures, recent results:{" "}
                {run.recent_outcomes.length
                  ? run.recent_outcomes.map((o) => outcome(o)).join(", ")
                  : "none yet"}
              </dd>
            </div>
            <div>
              <dt className="text-ink-muted">Provider / model</dt>
              <dd>
                {run.provider} / {run.model}
              </dd>
            </div>
            <div>
              <dt className="text-ink-muted">Prompt template</dt>
              <dd>{run.prompt_version}</dd>
            </div>
          </dl>

          <table className="w-full text-left text-sm">
            <caption className="mb-2 text-left font-bold">
              Attempts and validation
            </caption>
            <thead className="text-ink-muted">
              <tr>
                <th scope="col" className="py-1 pr-4">
                  Attempt
                </th>
                <th scope="col" className="py-1 pr-4">
                  Result
                </th>
                <th scope="col" className="py-1 pr-4">
                  Stopped at
                </th>
                <th scope="col" className="py-1 pr-4">
                  Reasons
                </th>
                <th scope="col" className="py-1">
                  Time
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {run.attempts.map((a) => (
                <tr key={a.attempt} className="align-top">
                  <th scope="row" className="py-2 pr-4 font-normal">
                    {a.attempt}
                  </th>
                  <td className="py-2 pr-4">
                    {a.status === "accepted"
                      ? "Passed all checks"
                      : a.status === "error"
                        ? "No usable response"
                        : "Rejected by validation"}
                  </td>
                  <td className="py-2 pr-4">
                    {a.failed_stage
                      ? (STAGE[a.failed_stage] ?? a.failed_stage)
                      : "—"}
                  </td>
                  <td className="py-2 pr-4">
                    {a.reason_codes.length
                      ? a.reason_codes.map(reasonLabel).join("; ")
                      : "—"}
                  </td>
                  <td className="py-2 tabular-nums">
                    {formatMs(a.latency_ms)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </li>
  );
}

export default async function AIGenerationsPage({
  params,
}: PageProps<"/clinician/patients/[patientId]/ai-generations">) {
  const { patientId } = await params;
  const runs = await backendGet(
    `/patients/${patientId}/ai-generations/runs`,
    z.array(AIRunSchema),
  );
  if (!runs) notFound();
  const counts = runs.reduce<Record<string, number>>(
    (acc, r) => ({ ...acc, [r.result]: (acc[r.result] ?? 0) + 1 }),
    {},
  );

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">AI audit log</h1>
        <p className="max-w-prose text-ink-muted">
          What the application recorded each time it asked the AI to personalise
          an exercise. Every suggestion is checked for format, clinical limits
          and safety before use; if checks fail, the patient receives a
          rule-based exercise instead. This is audit metadata recorded by the
          application. The AI gives no explanations; selection reasons are fixed
          codes it must choose from.
        </p>
      </div>

      {runs.length === 0 ? (
        <EmptyState icon={ShieldCheck} title="No AI activity recorded yet">
          Entries appear when the patient practises with AI personalisation
          enabled.
        </EmptyState>
      ) : (
        <>
          <p className="text-sm text-ink-muted">
            Last {runs.length} exercise slots: {counts.ai_generated ?? 0}{" "}
            accepted first time · {counts.ai_generated_after_retry ?? 0}{" "}
            accepted after retry · {counts.rule_based_used ?? 0} rule-based.
          </p>
          <ol className="flex flex-col gap-3">
            {runs.map((run, i) => (
              <Run
                key={`${run.session_id}-${run.position ?? run.created_at}-${i}`}
                run={run}
              />
            ))}
          </ol>
        </>
      )}
    </div>
  );
}
