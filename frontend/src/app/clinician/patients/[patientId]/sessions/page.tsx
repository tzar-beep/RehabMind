import { CalendarX } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { EmptyState } from "@/components/clinician/EmptyState";
import { OutcomeText } from "@/components/clinician/OutcomeBar";
import { StatusBadge } from "@/components/clinician/StatusBadge";
import { buttonClasses } from "@/components/ui/Button";
import { SessionPageSchema } from "@/lib/api/clinician";
import { backendGet } from "@/lib/api/server";
import {
  formatDateTime,
  formatDuration,
  responseMode,
  SESSION_STATUS,
} from "@/lib/format";

export const metadata: Metadata = { title: "Sessions" };

const PAGE_SIZE = 15;

export default async function SessionsPage({
  params,
  searchParams,
}: PageProps<"/clinician/patients/[patientId]/sessions">) {
  const { patientId } = await params;
  const pageParam = (await searchParams).page;
  const page = Math.max(
    1,
    Number(Array.isArray(pageParam) ? pageParam[0] : pageParam) || 1,
  );
  const data = await backendGet(
    `/patients/${patientId}/sessions?limit=${PAGE_SIZE}&offset=${(page - 1) * PAGE_SIZE}`,
    SessionPageSchema,
  );
  if (!data) notFound();
  const pages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));
  const base = `/clinician/patients/${patientId}/sessions`;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Session history</h1>
        <p className="text-ink-muted">
          {data.total} {data.total === 1 ? "session" : "sessions"} recorded,
          newest first.
        </p>
      </div>

      {data.total === 0 ? (
        <EmptyState icon={CalendarX} title="No sessions yet">
          Sessions appear here once the patient starts practising.
        </EmptyState>
      ) : (
        <>
          <div className="overflow-x-auto rounded-card border border-line bg-surface">
            <table className="w-full min-w-[820px] text-left">
              <caption className="sr-only">
                Practice sessions, page {page} of {pages}
              </caption>
              <thead className="border-b border-line text-sm text-ink-muted">
                <tr>
                  <th scope="col" className="px-5 py-3">
                    Started
                  </th>
                  <th scope="col" className="px-5 py-3">
                    Status
                  </th>
                  <th scope="col" className="px-5 py-3">
                    Answered
                  </th>
                  <th scope="col" className="px-5 py-3">
                    Results
                  </th>
                  <th scope="col" className="px-5 py-3">
                    Avg. difficulty
                  </th>
                  <th scope="col" className="px-5 py-3">
                    Answer methods
                  </th>
                  <th scope="col" className="px-5 py-3">
                    Duration
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {data.items.map((s) => (
                  <tr key={s.id}>
                    <th scope="row" className="px-5 py-3">
                      <Link
                        href={`${base}/${s.id}`}
                        className="font-bold text-accent underline-offset-4 hover:underline"
                      >
                        {formatDateTime(s.started_at)}
                      </Link>
                    </th>
                    <td className="px-5 py-3">
                      <StatusBadge
                        tone={
                          s.status === "completed"
                            ? "success"
                            : s.status === "active"
                              ? "info"
                              : "neutral"
                        }
                      >
                        {SESSION_STATUS[s.status] ?? s.status}
                      </StatusBadge>
                    </td>
                    <td className="px-5 py-3 tabular-nums">
                      {s.attempted} of {s.planned}
                    </td>
                    <td className="px-5 py-3 text-sm">
                      <OutcomeText o={s.outcomes} />
                    </td>
                    <td className="px-5 py-3 tabular-nums">
                      {s.avg_difficulty?.toFixed(1) ?? "—"}
                    </td>
                    <td className="px-5 py-3">
                      {s.modes.map(responseMode).join(", ") || "—"}
                    </td>
                    <td className="px-5 py-3">
                      {formatDuration(s.duration_s)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {pages > 1 && (
            <nav aria-label="Session pages" className="flex items-center gap-3">
              {page > 1 && (
                <Link
                  href={`${base}?page=${page - 1}`}
                  className={buttonClasses("secondary")}
                >
                  Newer
                </Link>
              )}
              <span className="text-ink-muted">
                Page {page} of {pages}
              </span>
              {page < pages && (
                <Link
                  href={`${base}?page=${page + 1}`}
                  className={buttonClasses("secondary")}
                >
                  Older
                </Link>
              )}
            </nav>
          )}
        </>
      )}
    </div>
  );
}
