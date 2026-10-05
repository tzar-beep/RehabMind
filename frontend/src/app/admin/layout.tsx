import { AppShell } from "@/components/AppShell";
import { requireRole } from "@/lib/api/server";

export default async function AdminLayout({ children }: LayoutProps<"/admin">) {
  const me = await requireRole("admin");
  return (
    <AppShell name={me.display_name} roleLabel="Administration" wide>
      {children}
    </AppShell>
  );
}
