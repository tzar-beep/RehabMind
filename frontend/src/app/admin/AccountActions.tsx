"use client";

import { Check, Copy, KeyRound, UserCheck, UserX } from "lucide-react";
import { useRouter } from "next/navigation";
import { useId, useState } from "react";
import { z } from "zod";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { ApiError, apiFetch } from "@/lib/api/client";
import { UserSummarySchema, type UserSummary } from "@/lib/api/schemas";

type Pending = "reset" | "toggle" | null;

/**
 * Per-account administration: add a patient to a clinician's care team, reset a lost
 * password (a new one is shown once) and disable / re-enable sign-in. Risky actions need
 * a second, explicit click.
 */
export function AccountActions({
  user,
  clinicians,
  isSelf,
}: {
  user: UserSummary;
  clinicians: { id: string; name: string }[];
  isSelf: boolean;
}) {
  const router = useRouter();
  const pickerId = useId();
  const [pending, setPending] = useState<Pending>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [password, setPassword] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const available = clinicians.filter((c) => !user.care_team.includes(c.name));
  const [clinician, setClinician] = useState(available[0]?.id ?? "");

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await action();
      setPending(null);
      router.refresh();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  const assign = () =>
    run(async () => {
      await apiFetch(
        `/admin/users/${user.id}/care-team`,
        { method: "POST", json: { clinician_user_id: clinician } },
        UserSummarySchema,
      );
    });
  const reset = () =>
    run(async () => {
      const r = await apiFetch(
        `/admin/users/${user.id}/password`,
        { method: "POST" },
        z.object({ initial_password: z.string() }),
      );
      setCopied(false);
      setPassword(r!.initial_password);
    });
  const toggle = () =>
    run(async () => {
      await apiFetch(
        `/admin/users/${user.id}/active`,
        { method: "PUT", json: { active: !user.is_active } },
        UserSummarySchema,
      );
    });

  return (
    <div className="flex min-w-64 flex-col gap-2">
      {error && <Alert tone="error">{error}</Alert>}

      {user.role === "patient" && available.length > 0 && (
        <div className="flex flex-wrap items-end gap-2">
          <div className="flex flex-col gap-1">
            <label htmlFor={pickerId} className="text-sm font-bold">
              {user.care_team.length ? "Add clinician" : "Assign clinician"}
            </label>
            <select
              id={pickerId}
              value={clinician}
              onChange={(e) => setClinician(e.target.value)}
              className="min-h-target rounded-control border-2 border-line-strong bg-surface px-3"
            >
              {available.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
          <Button variant="secondary" onClick={assign} busy={busy && !pending}>
            Assign
          </Button>
        </div>
      )}

      {password && (
        <div
          role="status"
          className="flex flex-col gap-2 rounded-control bg-success-soft p-3"
        >
          <p className="text-sm font-bold text-success">
            New password for {user.display_name}: shown only once
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <code className="rounded-control border border-line bg-surface px-3 py-1.5 font-mono tracking-wider">
              {password}
            </code>
            <Button
              variant="secondary"
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(password);
                  setCopied(true);
                } catch {
                  setCopied(false);
                }
              }}
            >
              {copied ? (
                <Check aria-hidden="true" size={18} />
              ) : (
                <Copy aria-hidden="true" size={18} />
              )}
              {copied ? "Copied" : "Copy"}
            </Button>
            <Button variant="quiet" onClick={() => setPassword(null)}>
              Done
            </Button>
          </div>
        </div>
      )}

      {pending ? (
        <div className="flex flex-wrap items-center gap-2 rounded-control bg-warning-soft p-3">
          <p className="w-full text-sm font-bold text-warning">
            {pending === "reset"
              ? `Reset ${user.display_name}'s password? They will be signed out everywhere.`
              : user.is_active
                ? `Disable ${user.display_name}? They will be signed out and cannot sign in.`
                : `Enable ${user.display_name} again?`}
          </p>
          <Button onClick={pending === "reset" ? reset : toggle} busy={busy}>
            {pending === "reset"
              ? "Yes, reset password"
              : user.is_active
                ? "Yes, disable"
                : "Yes, enable"}
          </Button>
          <Button
            variant="quiet"
            onClick={() => setPending(null)}
            disabled={busy}
          >
            Cancel
          </Button>
        </div>
      ) : (
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={() => setPending("reset")}>
            <KeyRound aria-hidden="true" size={18} />
            Reset password
          </Button>
          {!isSelf && (
            <Button variant="quiet" onClick={() => setPending("toggle")}>
              {user.is_active ? (
                <UserX aria-hidden="true" size={18} />
              ) : (
                <UserCheck aria-hidden="true" size={18} />
              )}
              {user.is_active ? "Disable" : "Enable"}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
