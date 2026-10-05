import { redirect } from "next/navigation";

// The patient list lives on the clinician dashboard.
export default function PatientsIndex() {
  redirect("/clinician");
}
