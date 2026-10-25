import { AppShell } from "@/components/AppShell";
import { requireRole } from "@/lib/api/server";

export default async function CarerLayout({ children }: LayoutProps<"/carer">) {
  const me = await requireRole("carer");
  return (
    <AppShell name={me.display_name} roleLabel="Family" wide>
      {children}
    </AppShell>
  );
}
