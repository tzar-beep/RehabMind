"use client";

import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const SECTIONS: Record<string, string> = {
  sessions: "Sessions",
  constraints: "Practice limits",
  "ai-generations": "AI audit log",
  "ai-pipeline": "AI pipeline",
};

/** Where you are inside a patient's record, every level clickable except the current one. */
export function Breadcrumbs({
  patientId,
  patientName,
}: {
  patientId: string;
  patientName: string;
}) {
  const pathname = usePathname();
  const base = `/clinician/patients/${patientId}`;
  const [section, detail] = pathname.slice(base.length + 1).split("/");
  const crumbs: { label: string; href: string }[] = [
    { label: "Patients", href: "/clinician" },
    { label: patientName, href: base },
  ];
  if (section && SECTIONS[section]) {
    crumbs.push({ label: SECTIONS[section], href: `${base}/${section}` });
  }
  if (section === "sessions" && detail) {
    crumbs.push({ label: "Session details", href: pathname });
  }
  return (
    <nav aria-label="Breadcrumb">
      <ol className="flex flex-wrap items-center gap-1.5 text-sm text-ink-muted">
        {crumbs.map((c, i) => {
          const current = i === crumbs.length - 1;
          return (
            <li key={c.href}>
              {current ? (
                <span aria-current="page" className="font-bold text-ink">
                  {c.label}
                </span>
              ) : (
                <Link
                  href={c.href}
                  className="rounded underline-offset-4 hover:text-ink hover:underline"
                >
                  {c.label}
                </Link>
              )}
              {!current && (
                <ChevronRight
                  aria-hidden="true"
                  size={14}
                  className="ml-1.5 inline align-[-2px]"
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
