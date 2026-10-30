import { BookOpen } from "lucide-react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { EmptyState } from "@/components/clinician/EmptyState";
import { StatusBadge } from "@/components/clinician/StatusBadge";
import { WordProgressListSchema, type WordProgress } from "@/lib/api/clinician";
import { backendGet } from "@/lib/api/server";
import { daysSince, errorType, outcome } from "@/lib/format";

export const metadata: Metadata = { title: "Words" };

const GROUPS = [
  {
    status: "needs_work",
    title: "Words to work on",
    description:
      "Named correctly less than half the time, over at least two tries.",
    tone: "warning",
  },
  {
    status: "learning",
    title: "Learning",
    description: "Mixed results, or not practised often enough to tell.",
    tone: "info",
  },
  {
    status: "secure",
    title: "Secure",
    description: "Named correctly the last three times.",
    tone: "success",
  },
] as const;

// Never colour alone: each result is a symbol with a text label.
const MARK: Record<string, { symbol: string; cls: string }> = {
  correct: { symbol: "✓", cls: "bg-success-soft text-success" },
  near_miss: { symbol: "~", cls: "bg-accent-soft text-accent-hover" },
  incorrect: { symbol: "✕", cls: "bg-warning-soft text-warning" },
  skipped: { symbol: "–", cls: "bg-canvas text-ink-muted border border-line" },
};

function lastPractised(iso: string) {
  const days = daysSince(iso) ?? 0;
  return days === 0 ? "today" : days === 1 ? "yesterday" : `${days} days ago`;
}

function WordCard({ w }: { w: WordProgress }) {
  return (
    <li className="flex gap-4 rounded-card border border-line bg-surface shadow-card p-4">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={w.image_url}
        alt=""
        width={72}
        height={72}
        className="size-18 shrink-0 rounded-control border border-line bg-white object-contain p-1"
      />
      <div className="flex min-w-0 flex-col gap-1.5">
        <p className="text-lg font-bold">{w.word}</p>
        <p className="text-sm text-ink-muted">
          {w.correct} of {w.attempts} right
          {w.close > 0 && ` · ${w.close} close`} · level {w.difficulty} ·{" "}
          {lastPractised(w.last_practised)}
        </p>
        <ol aria-label="Latest results, oldest first" className="flex gap-1">
          {w.recent.map((o, i) => (
            <li
              key={i}
              title={outcome(o)}
              className={`inline-flex size-6 items-center justify-center rounded text-sm font-bold ${MARK[o]?.cls ?? MARK.skipped.cls}`}
            >
              <span aria-hidden="true">{MARK[o]?.symbol ?? "?"}</span>
              <span className="sr-only">{outcome(o)}</span>
            </li>
          ))}
        </ol>
        {w.common_error && (
          <p className="text-sm">
            Usual error: <strong>{errorType(w.common_error)}</strong>
          </p>
        )}
      </div>
    </li>
  );
}

export default async function WordsPage({
  params,
}: PageProps<"/clinician/patients/[patientId]/words">) {
  const { patientId } = await params;
  const words = await backendGet(
    `/patients/${patientId}/words`,
    WordProgressListSchema,
  );
  if (!words) notFound();

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-bold">Words</h1>
        <p className="max-w-prose text-ink-muted">
          Every picture practised with a one-word answer (naming, sentence
          completion, repetition, recognition, category), since the latest fresh
          start. Use it to choose which words to practise in sessions.
        </p>
      </div>

      {words.length === 0 ? (
        <EmptyState icon={BookOpen} title="No words practised yet">
          Words appear here once the patient answers a one-word exercise.
        </EmptyState>
      ) : (
        <>
          <dl className="grid grid-cols-3 gap-3 sm:max-w-xl">
            {GROUPS.map((g) => (
              <div
                key={g.status}
                className="rounded-card border border-line bg-surface shadow-card p-4"
              >
                <dt className="text-sm text-ink-muted">{g.title}</dt>
                <dd className="text-2xl font-bold tabular-nums">
                  {words.filter((w) => w.status === g.status).length}
                </dd>
              </div>
            ))}
          </dl>
          {GROUPS.map((g) => {
            const group = words.filter((w) => w.status === g.status);
            if (group.length === 0) return null;
            return (
              <section
                key={g.status}
                aria-labelledby={`${g.status}-heading`}
                className="flex flex-col gap-3"
              >
                <div className="flex flex-wrap items-center gap-3">
                  <h2 id={`${g.status}-heading`} className="text-xl font-bold">
                    {g.title}
                  </h2>
                  <StatusBadge tone={g.tone}>
                    {group.length} {group.length === 1 ? "word" : "words"}
                  </StatusBadge>
                </div>
                <p className="text-ink-muted">{g.description}</p>
                <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {group.map((w) => (
                    <WordCard key={w.picture} w={w} />
                  ))}
                </ul>
              </section>
            );
          })}
        </>
      )}
    </div>
  );
}
