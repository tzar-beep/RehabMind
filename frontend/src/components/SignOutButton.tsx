"use client";

import { LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { apiFetch, markSigningOut } from "@/lib/api/client";

export function SignOutButton() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function signOut() {
    setBusy(true);
    markSigningOut();
    try {
      await apiFetch("/auth/logout", { method: "POST" });
    } finally {
      // Even if the call fails, leave the signed-in area; the server rejects stale sessions.
      router.replace("/login");
      router.refresh();
    }
  }

  return (
    <Button
      variant="quiet"
      onClick={signOut}
      busy={busy}
      className="whitespace-nowrap"
    >
      {!busy && <LogOut aria-hidden="true" size={18} />}
      Sign out
    </Button>
  );
}
