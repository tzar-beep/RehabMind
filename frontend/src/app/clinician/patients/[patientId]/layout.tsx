import Link from "next/link";
import { notFound } from "next/navigation";

import { PatientNav } from "@/components/clinician/PatientNav";
import { Avatar } from "@/components/ui/Avatar";
import { AIStatusSchema, PatientOverviewSchema } from "@/lib/api/clinician";
import { backendGet } from "@/lib/api/server";
import { formatDate } from "@/lib/format";

export default async function PatientLayout({
  children,
  params,
}: LayoutProps<"/clinician/patients/[patientId]">) {
  const { patientId } = await params;
  // The backend returns 404 unless this clinician is assigned to the patient.
  const [patient, aiStatus] = await Promise.all([
    backendGet(`/patients/${patientId}/overview`, PatientOverviewSchema),
    backendGet("/ai/status", AIStatusSchema),
  ]);
  if (!patient) notFound();

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-4">
        <nav aria-label="Breadcrumb">
          <ol className="flex gap-2 text-sm text-ink-muted">
            <li>
              <Link
                href="/clinician"
                className="underline-offset-4 hover:underline"
              >
                Patients
              </Link>
              <span aria-hidden="true"> /</span>
            </li>
            <li aria-current="page" className="font-bold text-ink">
              {patient.display_name}
            </li>
          </ol>
        </nav>
        <div className="flex items-center gap-5 rounded-card border border-line bg-surface p-6 shadow-card">
          <Avatar name={patient.display_name} size="lg" />
          <div>
            <p className="text-3xl font-bold">{patient.display_name}</p>
            <p className="text-ink-muted">
              Patient since {formatDate(patient.patient_since)} · Care team:{" "}
              {patient.care_team.join(", ")}
            </p>
          </div>
        </div>
        <PatientNav
          patientId={patientId}
          showPipeline={aiStatus?.demo_view ?? false}
        />
      </div>
      {children}
      <p className="border-t border-line pt-4 text-sm text-ink-muted">
        Academic prototype. Figures describe recorded practice activity only;
        they are not a diagnosis, prognosis or validated clinical measure.
      </p>
    </div>
  );
}
