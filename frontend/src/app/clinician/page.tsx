import {
  CalendarDays,
  CalendarCheck,
  CalendarX,
  ShieldAlert,
  Users,
} from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { z } from "zod";

import { EmptyState } from "@/components/clinician/EmptyState";
import { Facts, Section } from "@/components/clinician/Section";
import { StatusBadge } from "@/components/clinician/StatusBadge";
import { Avatar } from "@/components/ui/Avatar";
import {
  PatientListItemSchema,
  type PatientListItem,
} from "@/lib/api/clinician";
import { backendGet, requireRole } from "@/lib/api/server";
import { daysSince, formatDate, responseMode } from "@/lib/format";

export const metadata: Metadata = { title: "Patients" };

const RECENT_DAYS = 7;

function lastPractice(p: PatientListItem) {
  const days = daysSince(p.last_session_at);
  if (days === null)
    return <StatusBadge tone="neutral">No sessions yet</StatusBadge>;
  const when =
    days === 0 ? "Today" : days === 1 ? "Yesterday" : `${days} days ago`;
  return (
    <span className="flex flex-col">
      <span className="font-bold">{when}</span>
      <span className="text-sm text-ink-muted">
        {formatDate(p.last_session_at!)}
      </span>
    </span>
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

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-2">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Your patients</h1>
          <p className="mt-1 text-base text-ink-muted">
            {patients.length === 0
              ? "No patients assigned yet."
              : `${recent.length} of ${patients.length} practised in the last ${RECENT_DAYS} days. Recorded practice, not a clinical assessment.`}
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
              {
                icon: Users,
                label: "Assigned patients",
                value: patients.length,
              },
              {
                icon: CalendarCheck,
                label: `Practised in the last ${RECENT_DAYS} days`,
                value: recent.length,
              },
              {
                icon: CalendarX,
                label: `No practice in the last ${RECENT_DAYS} days`,
                value: patients.length - recent.length,
              },
              {
                icon: ShieldAlert,
                label: "Without practice limits",
                value: patients.filter((p) => !p.constraints).length,
                hint: "Practice cannot start until limits are set",
              },
            ]}
          />

          <Section
            id="patient-list"
            title="Patients"
            description="Sorted by care-team assignment."
          >
            <div className="overflow-x-auto rounded-card border border-line bg-surface shadow-card">
              <table className="w-full min-w-[720px] text-left">
                <caption className="sr-only">
                  Assigned patients and recent practice
                </caption>
                <thead className="border-b border-line text-sm font-normal text-ink-muted">
                  <tr>
                    <th scope="col" className="px-5 py-3">
                      Patient
                    </th>
                    <th scope="col" className="px-5 py-3">
                      Last practice
                    </th>
                    <th scope="col" className="px-5 py-3 text-right">
                      Sessions completed
                    </th>
                    <th scope="col" className="px-5 py-3">
                      Last 20 answers
                    </th>
                    <th scope="col" className="px-5 py-3">
                      Practice limits
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {patients.map((p) => (
                    <tr
                      key={p.id}
                      className="align-top"
                    >
                      <th scope="row" className="px-5 py-4">
                        <span className="flex items-center gap-3">
                          <Avatar name={p.display_name} />
                          <Link
                            href={`/clinician/patients/${p.id}`}
                            className="inline-flex min-h-target min-w-target items-center text-lg font-bold text-accent underline-offset-4 hover:underline"
                          >
                            {p.display_name}
                          </Link>
                        </span>
                      </th>
                      <td className="px-5 py-4">{lastPractice(p)}</td>
                      <td className="px-5 py-4 text-right tabular-nums">
                        {p.sessions_completed}
                      </td>
                      <td className="px-5 py-4">
                        {p.recent_responses ? (
                          <span className="flex w-40 flex-col gap-1.5">
                            <span className="tabular-nums">
                              {p.recent_correct} of {p.recent_responses} correct
                            </span>
                            <span
                              aria-hidden="true"
                              className="h-2 overflow-hidden rounded-full bg-line"
                            >
                              <span
                                className="block h-full rounded-full bg-chart"
                                style={{
                                  width: `${(p.recent_correct / p.recent_responses) * 100}%`,
                                }}
                              />
                            </span>
                          </span>
                        ) : (
                          <span className="text-ink-muted">No answers yet</span>
                        )}
                      </td>
                      <td className="px-5 py-4">
                        {p.constraints ? (
                          <span className="flex flex-col items-start gap-1">
                            <span className="rounded-full bg-accent-soft px-3 py-0.5 text-sm font-bold text-accent-hover">
                              Difficulty {p.constraints.min_difficulty}–
                              {p.constraints.max_difficulty}
                            </span>
                            <span className="text-sm text-ink-muted">
                              {p.constraints.allowed_response_modes
                                .map(responseMode)
                                .join(" or ")}{" "}
                              · v{p.constraints.version}
                            </span>
                          </span>
                        ) : (
                          <StatusBadge tone="warning">Not set</StatusBadge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>
        </>
      )}
    </div>
  );
}
