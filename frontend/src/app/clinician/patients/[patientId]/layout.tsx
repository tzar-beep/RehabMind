import { notFound } from "next/navigation";

import { Breadcrumbs } from "@/components/clinician/Breadcrumbs";
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
        <Breadcrumbs patientId={patientId} patientName={patient.display_name} />
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
