import {
  ChartLine,
  CircleCheck,
  CircleMinus,
  ClipboardList,
  Gauge,
  Keyboard,
  Lightbulb,
  ListChecks,
  MessageSquareText,
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
import { buttonClasses } from "@/components/ui/Button";
import {
  ConstraintVersionSchema,
  PatientOverviewSchema,
  TrendPointSchema,
} from "@/lib/api/clinician";
import { backendGet } from "@/lib/api/server";
import {
  formatDate,
  formatDateTime,
  formatMs,
  percent,
  responseMode,
} from "@/lib/format";

export const metadata: Metadata = { title: "Patient overview" };

const MIN_TREND_SESSIONS = 2;

export default async function PatientOverviewPage({
  params,
}: PageProps<"/clinician/patients/[patientId]">) {
  const { patientId } = await params;
  const [ov, trend, versions] = await Promise.all([
    backendGet(`/patients/${patientId}/overview`, PatientOverviewSchema),
    backendGet(`/patients/${patientId}/trends`, z.array(TrendPointSchema)),
    backendGet(
      `/patients/${patientId}/constraints/versions`,
      z.array(ConstraintVersionSchema),
    ),
  ]);
  if (!ov) notFound();
  const active = versions?.[0];
  const o = ov.outcomes;
  const attempted = o.correct + o.near_miss + o.incorrect + o.skipped;
  const base = `/clinician/patients/${patientId}`;

  return (
    <div className="flex flex-col gap-10">
      <h1 className="sr-only">{ov.display_name}: overview</h1>

      <Section
        id="limits"
        title="Current practice limits"
        description="Set by the care team. The AI and the rule-based generator always work inside these."
        action={
          <Link
            href={`${base}/constraints`}
            className={buttonClasses("secondary")}
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
          <EmptyState icon={ClipboardList} title="No practice limits set">
            The patient cannot start practice until a clinician sets limits.
          </EmptyState>
        )}
      </Section>

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
          <EmptyState icon={ChartLine} title="No practice recorded yet">
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
                  icon: Keyboard,
                  label: "Answer methods",
                  value: ov.by_mode.length,
                  hint:
                    ov.by_mode
                      .map(
                        (m) =>
                          `${responseMode(m.mode)}: ${m.correct}/${m.attempted} correct`,
                      )
                      .join(" · ") || "None yet",
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
                className={buttonClasses("secondary")}
              >
                View session history
              </Link>
            </div>
          </>
        )}
      </Section>
    </div>
  );
}
