import { CalendarDays, ChevronRight, Users } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { z } from "zod";

import { EmptyState } from "@/components/clinician/EmptyState";
import { Facts } from "@/components/clinician/Section";
import { StatusBadge } from "@/components/clinician/StatusBadge";
import { Avatar } from "@/components/ui/Avatar";
import {
  PatientListItemSchema,
  type PatientListItem,
} from "@/lib/api/clinician";
import { backendGet, requireRole } from "@/lib/api/server";
import { daysSince, responseMode } from "@/lib/format";
import { MagicCard } from "@/components/magicui/magic-card";

export const metadata: Metadata = { title: "Patients" };

const RECENT_DAYS = 7;
// Below this share correct, practice is mostly frustration (productive band 60-90%,
// docs/validation/personalization.md). Needs enough answers not to flag one bad day.
const STRUGGLING_BELOW = 0.4;
const STRUGGLING_MIN_ANSWERS = 10;

/** Why a patient needs the clinician's attention, if they do (most urgent first). */
function attention(p: PatientListItem): string | null {
  if (!p.constraints) return "No practice limits yet: practice cannot start";
  const days = daysSince(p.last_session_at);
  if (days === null) return "Has not practised yet";
  if (days >= RECENT_DAYS) return `No practice for ${days} days`;
  if (
    p.recent_responses >= STRUGGLING_MIN_ANSWERS &&
    p.recent_correct / p.recent_responses < STRUGGLING_BELOW
  )
    return `Struggling: ${p.recent_correct} of last ${p.recent_responses} answers correct. Consider easier practice limits`;
  return null;
}

function lastPractice(p: PatientListItem) {
  const days = daysSince(p.last_session_at);
  if (days === null) return "No sessions yet";
  if (days === 0) return "Practised today";
  if (days === 1) return "Practised yesterday";
  return `Last practised ${days} days ago`;
}

function PatientRow({ p }: { p: PatientListItem }) {
  const share = p.recent_responses ? p.recent_correct / p.recent_responses : 0;
  return (
    <li>
      {/* A soft spotlight follows the pointer across the row (Magic UI Magic Card). */}
      <MagicCard
        className="rounded-none border-0"
        gradientSize={260}
        gradientColor="var(--color-accent-soft)"
        gradientOpacity={0.9}
        gradientFrom="var(--color-accent)"
        gradientTo="var(--color-brand-glow)"
      >
        <div className="relative grid gap-x-8 gap-y-3 px-5 py-4 sm:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)_minmax(0,1fr)_auto] sm:items-center">
          <div className="flex min-w-0 items-center gap-3">
            <Avatar name={p.display_name} />
            <div className="min-w-0">
              {/* The name is the link; its hit area covers the whole row. */}
              <Link
                href={`/clinician/patients/${p.id}`}
                className="text-lg font-bold text-ink after:absolute after:inset-0 after:content-[''] hover:text-accent"
              >
                {p.display_name}
              </Link>
              <p className="text-sm text-ink-muted">
                {lastPractice(p)} · {p.sessions_completed}{" "}
                {p.sessions_completed === 1 ? "session" : "sessions"}
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="text-sm text-ink-muted">Last 20 answers</span>
            {p.recent_responses ? (
              <span className="flex items-center gap-3">
                <span
                  aria-hidden="true"
                  className="h-2 w-28 overflow-hidden rounded-full bg-line"
                >
                  <span
                    className="block h-full rounded-full bg-chart"
                    style={{ width: `${share * 100}%` }}
                  />
                </span>
                <span className="tabular-nums">
                  {p.recent_correct} of {p.recent_responses} correct
                </span>
              </span>
            ) : (
              <span className="text-ink-muted">—</span>
            )}
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="text-sm text-ink-muted">Practice limits</span>
            {p.constraints ? (
              <span>
                Levels {p.constraints.min_difficulty}–
                {p.constraints.max_difficulty} ·{" "}
                {p.constraints.allowed_response_modes
                  .map(responseMode)
                  .join(", ")}
              </span>
            ) : (
              <span>
                <StatusBadge tone="warning">Not set</StatusBadge>
              </span>
            )}
          </div>

          <ChevronRight
            aria-hidden="true"
            size={20}
            className="hidden text-ink-muted sm:block"
          />
        </div>
      </MagicCard>
    </li>
  );
}

export default async function ClinicianDashboard() {
  const me = await requireRole("clinician");
  const patients =
    (await backendGet(
      "/clinicians/me/patients",
      z.array(PatientListItemSchema),
    )) ?? [];
  const recent = patients.filter(
    (p) => (daysSince(p.last_session_at) ?? Infinity) < RECENT_DAYS,
  );
  const flagged = patients
    .map((p) => ({ p, reason: attention(p) }))
    .filter((x): x is { p: PatientListItem; reason: string } => !!x.reason);
  // Patients who need something first, then the most recently active.
  const ordered = [...patients].sort(
    (a, b) =>
      Number(!attention(a)) - Number(!attention(b)) ||
      (daysSince(a.last_session_at) ?? Infinity) -
        (daysSince(b.last_session_at) ?? Infinity),
  );

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-2">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Your patients</h1>
          <p className="mt-1 text-base text-ink-muted">
            {patients.length === 0
              ? "No patients assigned yet."
              : flagged.length
                ? `${flagged.length} of ${patients.length} need your attention. Recorded practice, not a clinical assessment.`
                : `${patients.length === 1 ? patients[0].display_name : `All ${patients.length} patients`} practised in the last ${RECENT_DAYS} days. Recorded practice, not a clinical assessment.`}
          </p>
        </div>
        <p className="flex items-center gap-2 text-sm text-ink-muted">
          <CalendarDays aria-hidden="true" size={16} />
          {new Intl.DateTimeFormat("en-GB", {
            weekday: "long",
            day: "numeric",
            month: "long",
          }).format(new Date())}
          <span className="sr-only">, signed in as {me.display_name}</span>
        </p>
      </div>

      {patients.length === 0 ? (
        <EmptyState icon={Users} title="No patients are assigned to you yet">
          Patients appear here once an administrator adds you to their care
          team.
        </EmptyState>
      ) : (
        <>
          <Facts
            items={[
              { label: "Assigned patients", value: patients.length },
              {
                label: `Practised in the last ${RECENT_DAYS} days`,
                value: recent.length,
              },
              {
                label: "Need your attention",
                value: flagged.length,
                hint: flagged.length
                  ? "Shown first in the list below"
                  : "Nothing to follow up",
              },
            ]}
          />

          {flagged.length > 0 && (
            <section aria-labelledby="attention-heading">
              <h2 id="attention-heading" className="mb-3 text-xl font-bold">
                To follow up
              </h2>
              <ul className="flex flex-col gap-2">
                {flagged.map(({ p, reason }) => (
                  <li
                    key={p.id}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-card border border-warning/30 bg-warning-soft px-5 py-3"
                  >
                    <span>
                      <span className="font-bold">{p.display_name}</span>:{" "}
                      {reason}
                    </span>
                    <Link
                      href={`/clinician/patients/${p.id}${p.constraints ? "" : "/constraints"}`}
                      className="inline-flex min-h-target shrink-0 items-center font-bold text-ink underline underline-offset-4"
                    >
                      {p.constraints ? "Open overview" : "Set practice limits"}
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section
            aria-labelledby="patient-list"
            className="flex flex-col gap-3"
          >
            <h2 id="patient-list" className="text-xl font-bold">
              Patients
            </h2>
            <ul className="divide-y divide-line overflow-hidden rounded-card border border-line bg-surface">
              {ordered.map((p) => (
                <PatientRow key={p.id} p={p} />
              ))}
            </ul>
          </section>
        </>
      )}
    </div>
  );
}
