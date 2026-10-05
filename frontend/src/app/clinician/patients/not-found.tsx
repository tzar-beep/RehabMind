// In the parent segment so it also catches notFound() thrown by [patientId]/layout.tsx.
import Link from "next/link";

import { buttonClasses } from "@/components/ui/Button";

export default function PatientNotFound() {
  return (
    <div className="flex flex-col items-start gap-4">
      <h1 className="text-3xl font-bold">Patient not available</h1>
      <p className="text-ink-muted">
        This patient does not exist or is not assigned to you. Access is limited
        to your own care team.
      </p>
      <Link href="/clinician" className={buttonClasses("secondary")}>
        Back to your patients
      </Link>
    </div>
  );
}
