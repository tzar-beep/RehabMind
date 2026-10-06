import { History } from "lucide-react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { z } from "zod";

import { ConstraintSummary } from "@/components/clinician/ConstraintSummary";
import { EmptyState } from "@/components/clinician/EmptyState";
import { Section } from "@/components/clinician/Section";
import { StatusBadge } from "@/components/clinician/StatusBadge";
import {
  ConstraintOptionsSchema,
  ConstraintVersionSchema,
} from "@/lib/api/clinician";
import { backendGet } from "@/lib/api/server";
import { formatDateTime } from "@/lib/format";

import { ConstraintEditor } from "./ConstraintEditor";
import { VersionCompare } from "./VersionCompare";

export const metadata: Metadata = { title: "Practice limits" };

export default async function ConstraintsPage({
  params,
}: PageProps<"/clinician/patients/[patientId]/constraints">) {
  const { patientId } = await params;
  const [versions, options] = await Promise.all([
    backendGet(
      `/patients/${patientId}/constraints/versions`,
      z.array(ConstraintVersionSchema),
    ),
    backendGet("/clinical/constraint-options", ConstraintOptionsSchema),
  ]);
  if (!versions || !options) notFound();
  const active = versions.find((v) => v.is_active) ?? null;

  return (
    <div className="flex flex-col gap-10">
      <div>
        <h1 className="text-2xl font-bold">Practice limits</h1>
        <p className="max-w-prose text-ink-muted">
          These clinician-set limits bound every exercise the patient receives,
          whether chosen by the AI or by the rule-based generator. They are
          enforced on the server and in the database. Versions are never edited:
          each change creates a new version.
        </p>
      </div>

      <Section id="active" title="Active version">
        {active ? (
          <div className="flex flex-col gap-4 rounded-card border border-line bg-surface p-6 shadow-card">
            <div className="flex flex-wrap items-center gap-3">
              <StatusBadge tone="success">
                Version {active.version} · active
              </StatusBadge>
              <span className="text-sm text-ink-muted">
                Created {formatDateTime(active.created_at)} by{" "}
                {active.created_by}
              </span>
            </div>
            <ConstraintSummary constraints={active} />
            {active.note && (
              <p className="text-ink-muted">Note: {active.note}</p>
            )}
          </div>
        ) : (
          <EmptyState icon={History} title="No practice limits yet">
            The patient cannot start practice until limits are set.
          </EmptyState>
        )}
        <ConstraintEditor
          patientId={patientId}
          current={active}
          options={options}
        />
      </Section>

      {versions.length > 0 && (
        <Section
          id="history"
          title="Version history"
          description="Read-only. Every version the patient has had, newest first."
        >
          {versions.length > 1 && <VersionCompare versions={versions} />}
          <ol className="flex flex-col gap-2">
            {versions.map((v) => (
              <li key={v.id}>
                <details className="rounded-card border border-line bg-surface px-5 py-3">
                  <summary className="flex min-h-target cursor-pointer flex-wrap items-center gap-3">
                    <span className="font-bold">Version {v.version}</span>
                    {v.is_active ? (
                      <StatusBadge tone="success">Active</StatusBadge>
                    ) : (
                      <StatusBadge tone="neutral">Superseded</StatusBadge>
                    )}
                    <span className="text-sm text-ink-muted">
                      {formatDateTime(v.created_at)} · {v.created_by} ·
                      difficulty {v.min_difficulty}–{v.max_difficulty}
                    </span>
                  </summary>
                  <div className="flex flex-col gap-3 py-4">
                    <ConstraintSummary constraints={v} />
                    {v.note && <p className="text-ink-muted">Note: {v.note}</p>}
                  </div>
                </details>
              </li>
            ))}
          </ol>
        </Section>
      )}
    </div>
  );
}
