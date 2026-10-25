import {
  ChartLine,
  CircleCheck,
  CircleMinus,
  ClipboardList,
  Gauge,
  Keyboard,
  Lightbulb,
  ListChecks,
  MessageCircleHeart,
  MessageSquareText,
  Shapes,
  Timer,
} from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { z } from "zod";

import { ConstraintSummary } from "@/components/clinician/ConstraintSummary";
import { EmptyState } from "@/components/clinician/EmptyState";
import {
  AnswersBySessionChart,
  DifficultyBySessionChart,
} from "@/components/clinician/TrendCharts";
import { Facts, Section } from "@/components/clinician/Section";
import { StatusBadge } from "@/components/clinician/StatusBadge";
import { Alert } from "@/components/ui/Alert";
import { buttonClasses } from "@/components/ui/Button";
import {
  AIStatusSchema,
  ScriptSummarySchema,
  ConstraintVersionSchema,
  PatientOverviewSchema,
  ProgressSummarySchema,
  TrendPointSchema,
} from "@/lib/api/clinician";
import { MOODS } from "@/lib/moods";
import { MoodDaySchema } from "@/lib/api/schemas";
import { backendGet } from "@/lib/api/server";
import {
  DIFFICULTY_RATING,
  daysSince,
  errorType,
  formatDate,
  formatDateTime,
  formatMs,
  percent,
  responseMode,
} from "@/lib/format";

import { ProgressSummaryCard } from "./ProgressSummaryCard";
import { ResetProgress } from "./ResetProgress";

export const metadata: Metadata = { title: "Patient overview" };

const MIN_TREND_SESSIONS = 2;

export default async function PatientOverviewPage({
  params,
}: PageProps<"/clinician/patients/[patientId]">) {
  const { patientId } = await params;
  const [ov, trend, versions, aiSummary, aiStatus, phrases, moods] =
    await Promise.all([
      backendGet(`/patients/${patientId}/overview`, PatientOverviewSchema),
      backendGet(`/patients/${patientId}/trends`, z.array(TrendPointSchema)),
      backendGet(
        `/patients/${patientId}/constraints/versions`,
        z.array(ConstraintVersionSchema),
      ),
      backendGet(
        `/patients/${patientId}/progress-summary`,
        ProgressSummarySchema.nullable(),
      ),
      backendGet("/ai/status", AIStatusSchema),
      backendGet(
        `/patients/${patientId}/phrases`,
        z.array(ScriptSummarySchema),
      ),
      backendGet(`/patients/${patientId}/moods`, z.array(MoodDaySchema)),
    ]);
  if (!ov) notFound();
  const lowDays = (moods ?? []).filter(
    (m) => m.mood === "low" && (daysSince(m.day) ?? 99) < 7,
  ).length;
  const practisedPhrases = (phrases ?? []).filter((p) => p.times_total > 0);
  const active = versions?.[0];
  const o = ov.outcomes;
  const errors = Object.entries(ov.error_profile)
    .filter(([t]) => t !== "correct")
    .sort((a, b) => b[1] - a[1]);
  const topError = errors[0];
  const ratedSessions = Object.values(ov.difficulty_ratings).reduce(
    (a, b) => a + b,
    0,
  );
  const errorBreakdown = errors
    .map(([t, n]) => `${errorType(t)}: ${n}`)
    .join(" · ");
  const attempted = o.correct + o.near_miss + o.incorrect + o.skipped;
  const base = `/clinician/patients/${patientId}`;

  return (
    <div className="flex flex-col gap-10">
      <h1 className="sr-only">{ov.display_name}: overview</h1>

      {ov.last_reset && (
        <Alert tone="info">
          <strong>Fresh start on {formatDateTime(ov.last_reset.at)}</strong>
          {ov.last_reset.by && <> by {ov.last_reset.by}</>}: &ldquo;
          {ov.last_reset.reason}&rdquo;. Figures below count practice since
          then; earlier sessions stay in the session history.
        </Alert>
      )}

      <Section
        id="activity"
        title="Practice activity"
        description={
          ov.last_session_at
            ? `All recorded sessions, ${formatDate(ov.first_session_at!)} to ${formatDate(ov.last_session_at)}.`
            : undefined
        }
      >
        {ov.sessions_total === 0 ? (
          <EmptyState
            icon={ChartLine}
            title="No practice recorded yet"
            action={
              active
                ? undefined
                : {
                    href: `${base}/constraints`,
                    label: "Set practice limits first",
                  }
            }
          >
            Activity appears here after the patient completes their first
            exercise.
          </EmptyState>
        ) : (
          <>
            <Facts
              items={[
                {
                  icon: ListChecks,
                  label: "Sessions completed",
                  value: ov.sessions_completed,
                  hint: `${ov.sessions_stopped_early} stopped early${ov.has_active_session ? " · 1 in progress" : ""}`,
                },
                {
                  icon: MessageSquareText,
                  label: "Answers given",
                  value: attempted,
                },
                {
                  icon: CircleCheck,
                  label: "Correct",
                  value: percent(o.correct, attempted),
                  hint: `${o.correct} correct · ${o.near_miss} close`,
                },
                {
                  icon: CircleMinus,
                  label: "Incorrect or skipped",
                  value: o.incorrect + o.skipped,
                  hint: `${o.incorrect} incorrect · ${o.skipped} skipped`,
                },
                {
                  icon: Lightbulb,
                  label: "Answers after a hint",
                  value: ov.hinted_responses,
                  hint: "Correct-with-hint holds the level",
                },
                {
                  icon: Timer,
                  label: "Median time to answer",
                  value: formatMs(ov.median_latency_ms),
                  hint: "Skipped answers excluded",
                },
                {
                  icon: Gauge,
                  label: "Current working level",
                  value: ov.current_working_difficulty ?? "—",
                  hint: "Set by the progression rule, within limits",
                },
                {
                  icon: MessageCircleHeart,
                  label: "How sessions felt (patient)",
                  value: ratedSessions || "—",
                  hint:
                    Object.entries(ov.difficulty_ratings)
                      .map(([r, n]) => `${DIFFICULTY_RATING[r] ?? r}: ${n}`)
                      .join(" · ") || "No ratings yet",
                },
                {
                  icon: Shapes,
                  label: "Most common naming error",
                  value: topError ? errorType(topError[0]) : "—",
                  hint: errorBreakdown || "No naming errors yet",
                },
                {
                  icon: Keyboard,
                  label: "Answer methods",
                  value: ov.by_mode.length,
                  hint:
                    ov.by_mode
                      .map(
                        (m) =>
                          `${responseMode(m.mode)}: ${m.correct}/${m.attempted} correct`,
                      )
                      .join(" · ") +
                      (ov.uncertain_speech_matches
                        ? ` · ${ov.uncertain_speech_matches} speech answer(s) to check`
                        : "") +
                      (ov.speech_misheard
                        ? ` · ${ov.speech_misheard} misheard (the patient said no)`
                        : "") || "None yet",
                },
              ]}
            />
            {trend && trend.length >= MIN_TREND_SESSIONS ? (
              <div className="grid gap-6 lg:grid-cols-2">
                <AnswersBySessionChart trend={trend} />
                <DifficultyBySessionChart trend={trend} />
              </div>
            ) : (
              <EmptyState
                icon={ChartLine}
                title="Not enough sessions for trends yet"
              >
                Trends appear once at least {MIN_TREND_SESSIONS} sessions
                include answers.
              </EmptyState>
            )}
            <div>
              <Link
                href={`${base}/sessions`}
                className={`${buttonClasses("secondary")} no-print`}
              >
                View session history
              </Link>
            </div>
          </>
        )}
      </Section>

      <Section
        id="phrases"
        title="Everyday phrases"
        description="Scripts practised at home in the last 14 days. Lines said are the patient's own report."
      >
        {practisedPhrases.length ? (
          <ul className="divide-y divide-line overflow-hidden rounded-card border border-line bg-surface">
            {practisedPhrases.map((p) => (
              <li
                key={p.id}
                className="flex flex-wrap items-center justify-between gap-x-6 gap-y-1 px-5 py-3"
              >
                <span className="font-bold">{p.title}</span>
                <span className="text-ink-muted tabular-nums">
                  {p.times_recent} {p.times_recent === 1 ? "time" : "times"}
                  {p.lines_said_share !== null &&
                    ` · ${Math.round(p.lines_said_share * 100)}% of lines said`}
                  {p.last_practised &&
                    ` · last ${formatDate(p.last_practised)}`}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-ink-muted">No everyday phrases practised yet.</p>
        )}
      </Section>

      <Section
        id="wellbeing"
        title="Wellbeing"
        description="How the patient said they felt, one tap a day on their home page (last 14 days)."
      >
        {moods && moods.length ? (
          <div className="flex flex-col gap-3">
            {lowDays >= 3 && (
              <div>
                <StatusBadge tone="warning">
                  Low mood on {lowDays} of the last 7 days
                </StatusBadge>
              </div>
            )}
            <ol className="flex flex-wrap gap-2">
              {moods.map((m) => {
                const { Icon, label } =
                  MOODS.find((x) => x.mood === m.mood) ?? MOODS[1];
                return (
                  <li
                    key={m.day}
                    className="flex w-20 flex-col items-center gap-1 rounded-control border border-line bg-surface py-2"
                  >
                    <Icon
                      aria-hidden="true"
                      size={22}
                      className={
                        m.mood === "low"
                          ? "text-warning"
                          : m.mood === "good"
                            ? "text-success"
                            : "text-ink-muted"
                      }
                    />
                    <span className="text-xs text-ink-muted">
                      {formatDate(m.day)}
                    </span>
                    <span className="sr-only">{label}</span>
                  </li>
                );
              })}
            </ol>
          </div>
        ) : (
          <p className="text-ink-muted">No check-ins yet.</p>
        )}
      </Section>

      <Section
        id="limits"
        title="Current practice limits"
        description="Set by the care team. The AI and the rule-based generator always work inside these."
        action={
          <Link
            href={`${base}/constraints`}
            className={`${buttonClasses("secondary")} no-print`}
          >
            {active ? "Review or create new version" : "Set practice limits"}
          </Link>
        }
      >
        {active ? (
          <div className="flex flex-col gap-4 rounded-card border border-line bg-surface p-6 shadow-card">
            <div className="flex flex-wrap items-center gap-3">
              <StatusBadge tone="success">
                Active: version {active.version}
              </StatusBadge>
              <span className="text-sm text-ink-muted">
                Created {formatDateTime(active.created_at)} by{" "}
                {active.created_by}
              </span>
            </div>
            <ConstraintSummary constraints={active} />
          </div>
        ) : (
          <EmptyState
            icon={ClipboardList}
            title="No practice limits set"
            action={{
              href: `${base}/constraints`,
              label: "Set practice limits",
            }}
          >
            The patient cannot start practice until a clinician sets limits.
          </EmptyState>
        )}
      </Section>

      <Section
        id="ai-summary"
        title="AI progress summary"
        description="A short written summary of the figures above, per rehabilitation objective."
      >
        <ProgressSummaryCard
          patientId={patientId}
          initial={aiSummary}
          status={aiStatus}
        />
      </Section>

      <Section
        id="fresh-start"
        title="Fresh start"
        description="Reset progress when starting a new therapy block. Nothing is deleted, and the reset is recorded."
      >
        <ResetProgress patientId={patientId} patientName={ov.display_name} />
      </Section>
    </div>
  );
}
