import type { Metadata } from "next";
import { z } from "zod";

import { PatientSchema } from "@/lib/api/schemas";
import { backendGet } from "@/lib/api/server";

export const metadata: Metadata = { title: "Patients" };

export default async function ClinicianHome() {
  const patients = (await backendGet("/clinicians/me/patients", z.array(PatientSchema))) ?? [];

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-3xl font-bold">Your patients</h1>
      {patients.length === 0 ? (
        <p className="rounded-card border border-dashed border-line-strong bg-surface p-8 text-ink-muted">
          No patients are assigned to you yet.
        </p>
      ) : (
        <ul className="divide-y divide-line rounded-card border border-line bg-surface">
          {patients.map((p) => (
            <li key={p.id} className="flex items-center justify-between px-6 py-4">
              <span className="text-lg font-bold">{p.display_name}</span>
              <span className="text-sm text-ink-muted">No sessions yet</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
