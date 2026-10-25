"use client";

import { ShieldCheck } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

export function PatientNav({ patientId }: { patientId: string }) {
  const pathname = usePathname();
  const base = `/clinician/patients/${patientId}`;
  // The clinician's work: how practice is going, which words, and the plan. How the AI
  // reached its choices is one step away (AI review), not a main tab.
  const tabs = [
    { href: base, label: "Overview", exact: true },
    { href: `${base}/sessions`, label: "Sessions" },
    { href: `${base}/words`, label: "Words" },
    { href: `${base}/constraints`, label: "Plan" },
  ];
  const aiActive =
    pathname.startsWith(`${base}/ai-generations`) ||
    pathname.startsWith(`${base}/ai-pipeline`);
  return (
    <nav aria-label="Patient sections" className="border-b border-line">
      <ul className="-mb-px flex flex-wrap items-center gap-1">
        {tabs.map((t) => {
          const active = t.exact
            ? pathname === t.href
            : pathname.startsWith(t.href);
          return (
            <li key={t.href}>
              <Link
                href={t.href}
                aria-current={active ? "page" : undefined}
                className={
                  "inline-flex min-h-target items-center border-b-4 px-4 font-bold " +
                  (active
                    ? "border-accent text-ink"
                    : "border-transparent text-ink-muted hover:border-line-strong hover:text-ink")
                }
              >
                {t.label}
              </Link>
            </li>
          );
        })}
        <li className="ml-auto">
          <Link
            href={`${base}/ai-generations`}
            aria-current={aiActive ? "page" : undefined}
            className={
              "inline-flex min-h-target items-center gap-1.5 border-b-4 px-3 text-sm " +
              (aiActive
                ? "border-accent font-bold text-ink"
                : "border-transparent text-ink-muted hover:text-ink")
            }
          >
            <ShieldCheck aria-hidden="true" size={16} />
            AI review
          </Link>
        </li>
      </ul>
    </nav>
  );
}
