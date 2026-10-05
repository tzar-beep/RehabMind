"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function PatientNav({ patientId }: { patientId: string }) {
  const pathname = usePathname();
  const base = `/clinician/patients/${patientId}`;
  const tabs = [
    { href: base, label: "Overview", exact: true },
    { href: `${base}/sessions`, label: "Sessions" },
    { href: `${base}/constraints`, label: "Practice limits" },
    { href: `${base}/ai-generations`, label: "AI audit log" },
  ];
  return (
    <nav aria-label="Patient sections" className="border-b border-line">
      <ul className="-mb-px flex flex-wrap gap-1">
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
      </ul>
    </nav>
  );
}
