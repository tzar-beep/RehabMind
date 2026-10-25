"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { apiFetch } from "@/lib/api/client";

/** Stop sharing with a family member: asks once more, because only an admin can undo it. */
export function StopSharing({
  userId,
  name,
}: {
  userId: string;
  name: string;
}) {
  const router = useRouter();
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  if (!confirming)
    return (
      <Button variant="secondary" onClick={() => setConfirming(true)}>
        Stop sharing
      </Button>
    );
  return (
    <div
      role="group"
      aria-label={`Stop sharing with ${name}?`}
      className="flex flex-wrap items-center gap-2"
    >
      <span className="font-bold">Stop sharing with {name}?</span>
      <Button
        busy={busy}
        onClick={async () => {
          setBusy(true);
          await apiFetch(`/practice/my-information/family/${userId}`, {
            method: "DELETE",
          }).catch(() => undefined);
          router.refresh();
        }}
      >
        Yes, stop
      </Button>
      <Button variant="quiet" onClick={() => setConfirming(false)}>
        Cancel
      </Button>
    </div>
  );
}
