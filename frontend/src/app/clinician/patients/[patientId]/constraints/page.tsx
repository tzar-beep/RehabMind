import { History } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { z } from "zod";

import { ConstraintSummary } from "@/components/clinician/ConstraintSummary";
import { EmptyState } from "@/components/clinician/EmptyState";
import { Section } from "@/components/clinician/Section";
import { StatusBadge } from "@/components/clinician/StatusBadge";
import {
  ConstraintOptionsSchema,
  ConstraintVersionSchema,
  type ConstraintVersion,
} from "@/lib/api/clinician";
import { backendGet } from "@/lib/api/server";
import { formatDateTime } from "@/lib/format";

import { ConstraintEditor } from "./ConstraintEditor";
import { VersionCompare } from "./VersionCompare";

export const metadata: Metadata = { title: "Practice limits" };

// The history can grow long; the newest few are listed, the rest behind "Show all".
const RECENT_VERSIONS = 6;
const COMPARE_VERSIONS = 20;

function VersionRow({ v }: { v: ConstraintVersion }) {
  return (
    <li>
      <details className="px-5 py-1">
        <summary className="flex min-h-target cursor-pointer flex-wrap items-center gap-3">
          <span className="font-bold">Version {v.version}</span>
          {v.is_active ? (
            <StatusBadge tone="success">Active</StatusBadge>
          ) : (
            <StatusBadge tone="neutral">Superseded</StatusBadge>
          )}
          <span className="text-sm text-ink-muted">
            {formatDateTime(v.created_at)} · {v.created_by} · levels{" "}
            {v.min_difficulty}–{v.max_difficulty}
          </span>
        </summary>
        <div className="flex flex-col gap-3 pt-2 pb-4">
          <ConstraintSummary constraints={v} />
          {v.note && <p className="text-ink-muted">Note: {v.note}</p>}
        </div>
      </details>
    </li>
  );
}

export default async function ConstraintsPage({
  params,
  searchParams,
}: PageProps<"/clinician/patients/[patientId]/constraints">) {
  const { patientId } = await params;
  const showAll = (await searchParams).history === "all";
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
          Every exercise, AI-written or rule-based, stays inside these limits.
          Changes create a new version; old versions are kept.
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
          {versions.length > 1 && (
            <VersionCompare
              versions={
                showAll ? versions : versions.slice(0, COMPARE_VERSIONS)
              }
            />
          )}
          <ol className="divide-y divide-line overflow-hidden rounded-card border border-line bg-surface">
            {(showAll ? versions : versions.slice(0, RECENT_VERSIONS)).map(
              (v) => (
                <VersionRow key={v.id} v={v} />
              ),
            )}
          </ol>
          {!showAll && versions.length > RECENT_VERSIONS && (
            <Link
              href="?history=all#history"
              className="w-fit py-2 font-bold text-accent underline-offset-4 hover:underline"
            >
              Show all {versions.length} versions
            </Link>
          )}
        </Section>
      )}
    </div>
  );
}
