import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { OutcomeText } from "@/components/clinician/OutcomeBar";
import { Facts } from "@/components/clinician/Section";
import { StatusBadge } from "@/components/clinician/StatusBadge";
import { SessionDetailSchema, type ExerciseDetail } from "@/lib/api/clinician";
import { backendGet } from "@/lib/api/server";
import {
  exerciseType,
  formatDateTime,
  formatDuration,
  formatMs,
  outcome,
  responseMode,
  SESSION_STATUS,
  SOURCE,
  SPEECH_ATTEMPT_REASON,
} from "@/lib/format";

export const metadata: Metadata = { title: "Session detail" };

function ResultBadge({ ex }: { ex: ExerciseDetail }) {
  const tone =
    ex.outcome === "correct"
      ? "success"
      : ex.outcome === "near_miss"
        ? "info"
        : "neutral";
  return <StatusBadge tone={tone}>{outcome(ex.outcome)}</StatusBadge>;
}

function Transcript({ ex }: { ex: ExerciseDetail }) {
  const q = ex.transcript_quality;
  return (
    <div className="flex flex-col gap-1 text-sm">
      {ex.response_mode === "speech" ? (
        <>
          <p>
            <span className="text-ink-muted">
              Transcript (automatic, may contain errors):{" "}
            </span>
            <span className="font-bold">&ldquo;{ex.response_text}&rdquo;</span>
          </p>
          {q && (
            <p className="text-ink-muted">
              Recognition: no-speech probability {q.no_speech_prob ?? "—"},
              average log-probability {q.avg_logprob ?? "—"}
              {q.low_confidence_words.length > 0 &&
                ` · uncertain words: ${q.low_confidence_words.join(", ")}`}
            </p>
          )}
        </>
      ) : (
        <p>
          <span className="text-ink-muted">Typed answer: </span>
          <span className="font-bold">
            {ex.response_text ? `“${ex.response_text}”` : "(no text)"}
          </span>
        </p>
      )}
    </div>
  );
}

export default async function SessionDetailPage({
  params,
}: PageProps<"/clinician/patients/[patientId]/sessions/[sessionId]">) {
  const { patientId, sessionId } = await params;
  const data = await backendGet(
    `/patients/${patientId}/sessions/${sessionId}`,
    SessionDetailSchema,
  );
  if (!data) notFound();
  const s = data.session;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Link
          href={`/clinician/patients/${patientId}/sessions`}
          className="text-sm text-accent underline-offset-4 hover:underline"
        >
          ← All sessions
        </Link>
        <h1 className="mt-2 text-2xl font-bold">
          Session on {formatDateTime(s.started_at)}
        </h1>
        <p className="text-ink-muted">
          Exercises in the order they were shown. No audio is kept: recordings
          are deleted after transcription.
        </p>
      </div>

      <Facts
        items={[
          { label: "Status", value: SESSION_STATUS[s.status] ?? s.status },
          { label: "Answered", value: `${s.attempted} of ${s.planned}` },
          {
            label: "Average difficulty",
            value: s.avg_difficulty?.toFixed(1) ?? "—",
          },
          { label: "Duration", value: formatDuration(s.duration_s) },
        ]}
      />
      <p>
        <OutcomeText o={s.outcomes} />
      </p>

      <ol className="flex flex-col gap-3">
        {data.exercises.map((ex) => (
          <li
            key={ex.position}
            className="grid gap-4 rounded-card border border-line bg-surface p-5 sm:grid-cols-[96px_1fr]"
          >
            {ex.image_url && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={ex.image_url}
                alt={`Picture: ${ex.target}`}
                width={96}
                height={96}
                className="rounded-control border border-line p-3"
              />
            )}
            <div className="flex flex-col gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="font-bold">
                  {ex.position}. {exerciseType(ex.exercise_type)}: {ex.target}
                </h2>
                <ResultBadge ex={ex} />
              </div>
              <p className="text-sm text-ink-muted">
                Difficulty {ex.difficulty} · {ex.category ?? "—"} ·{" "}
                {SOURCE[ex.source] ?? ex.source} · prompt &ldquo;{ex.prompt}
                &rdquo;
              </p>
              {ex.outcome ? (
                <>
                  <Transcript ex={ex} />
                  <p className="text-sm text-ink-muted">
                    {responseMode(ex.response_mode ?? "")} · time to answer{" "}
                    {formatMs(ex.latency_ms)} ·{" "}
                    {ex.hints_used
                      ? `${ex.hints_used} hint(s) used`
                      : "no hints"}
                    {ex.match_type &&
                      ` · scoring rule: ${ex.match_type.replaceAll("_", " ")}`}
                  </p>
                </>
              ) : (
                <p className="text-sm text-ink-muted">
                  {ex.status === "cancelled"
                    ? "Not answered (session stopped)."
                    : "Not answered."}
                </p>
              )}
              {ex.speech_attempts.length > 0 && (
                <p className="text-sm text-ink-muted">
                  Recordings: {ex.speech_attempts.length} —{" "}
                  {ex.speech_attempts
                    .map((a) =>
                      a.status === "done"
                        ? "transcribed"
                        : `not scored (${SPEECH_ATTEMPT_REASON[a.reason ?? ""] ?? a.status})`,
                    )
                    .join("; ")}
                  . All deleted after processing.
                </p>
              )}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
