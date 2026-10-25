import { notFound } from "next/navigation";

import { Breadcrumbs } from "@/components/clinician/Breadcrumbs";
import { PatientNav } from "@/components/clinician/PatientNav";
import { PrintButton } from "@/components/clinician/PrintButton";
import { Alert } from "@/components/ui/Alert";
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
  // Only a configured local model can be "offline"; a deliberately AI-free setup is not.
  const aiOffline =
    aiStatus?.provider === "ollama" &&
    !(aiStatus.reachable && aiStatus.model_available);

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-3">
        <Breadcrumbs patientId={patientId} patientName={patient.display_name} />
        <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
          <p className="flex items-center gap-3 text-2xl font-bold tracking-tight">
            <Avatar name={patient.display_name} size="sm" />
            {patient.display_name}
          </p>
          <p className="text-base text-ink-muted">
            Patient since {formatDate(patient.patient_since)} · Care team:{" "}
            {patient.care_team.join(", ")}
          </p>
          <div className="ml-auto">
            <PrintButton />
          </div>
        </div>
        <PatientNav
          patientId={patientId}
          showPipeline={aiStatus?.demo_view ?? false}
        />
      </div>
      {aiOffline && (
        <Alert tone="warning">
          <strong>AI is offline.</strong> Exercises, feedback and summaries use
          the rule-based versions until the local model{" "}
          {aiStatus?.model ? `(${aiStatus.model}) ` : ""}is running again.
          Practice is not affected.
        </Alert>
      )}
      {children}
      <p className="border-t border-line pt-4 text-sm text-ink-muted">
        Academic prototype. Figures describe recorded practice activity only;
        they are not a diagnosis, prognosis or validated clinical measure.
      </p>
    </div>
  );
}
