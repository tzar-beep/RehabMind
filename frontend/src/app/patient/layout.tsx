import { AppShell } from "@/components/AppShell";
import { requireRole } from "@/lib/api/server";

export default async function PatientLayout({
  children,
}: LayoutProps<"/patient">) {
  const me = await requireRole("patient");
  return <AppShell name={me.display_name}>{children}</AppShell>;
}
