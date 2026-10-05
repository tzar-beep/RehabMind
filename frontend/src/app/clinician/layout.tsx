import { AppShell } from "@/components/AppShell";
import { requireRole } from "@/lib/api/server";

export default async function ClinicianLayout({
  children,
}: LayoutProps<"/clinician">) {
  const me = await requireRole("clinician");
  return (
    <AppShell name={me.display_name} roleLabel="Clinician" wide>
      {children}
    </AppShell>
  );
}
