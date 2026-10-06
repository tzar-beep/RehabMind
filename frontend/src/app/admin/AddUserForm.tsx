"use client";

import { Check, Copy, KeyRound, UserPlus } from "lucide-react";
import { useRouter } from "next/navigation";
import { useId, useRef, useState, type FormEvent } from "react";
import { z } from "zod";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { TextField } from "@/components/ui/TextField";
import { ApiError, apiFetch } from "@/lib/api/client";
import { UserSummarySchema } from "@/lib/api/schemas";

const CreatedSchema = z.object({
  user: UserSummarySchema,
  initial_password: z.string(),
});

const ROLES = [
  { value: "patient", label: "Patient" },
  { value: "clinician", label: "Clinician" },
  { value: "admin", label: "Administrator" },
] as const;

type Created = z.infer<typeof CreatedSchema>;

/** Create an account. The generated first password is shown here once and never again. */
export function AddUserForm({
  clinicians,
}: {
  clinicians: { id: string; name: string }[];
}) {
  const router = useRouter();
  const [role, setRole] = useState<string>("patient");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState<Created | null>(null);
  const [copied, setCopied] = useState(false);
  const clinicianId = useId();
  const resultRef = useRef<HTMLDivElement>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const email = String(data.get("email") ?? "").trim();
    const display_name = String(data.get("name") ?? "").trim();
    const clinician = String(data.get("clinician") ?? "");
    if (!email || !display_name) {
      setError("Please enter a name and an email address.");
      return;
    }
    setBusy(true);
    setError(null);
    setCopied(false);
    try {
      const result = await apiFetch(
        "/admin/users",
        {
          method: "POST",
          json: {
            email,
            display_name,
            role,
            clinician_user_id:
              role === "patient" && clinician ? clinician : null,
          },
        },
        CreatedSchema,
      );
      setCreated(result!);
      form.reset();
      setRole("patient");
      router.refresh();
      requestAnimationFrame(() => resultRef.current?.focus());
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.message
          : "Something went wrong. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function copy() {
    if (!created) return;
    try {
      await navigator.clipboard.writeText(created.initial_password);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {created && (
        <div
          ref={resultRef}
          tabIndex={-1}
          role="status"
          className="flex flex-col gap-4 rounded-card border-2 border-success/40 bg-success-soft p-6"
        >
          <p className="flex items-center gap-2 text-lg font-bold text-success">
            <Check aria-hidden="true" size={22} />
            Account created for {created.user.display_name} (
            {created.user.email})
          </p>
          <div className="flex flex-col gap-2">
            <p className="flex items-center gap-2 font-bold">
              <KeyRound aria-hidden="true" size={18} />
              First password: shown only once
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <code className="rounded-control border border-line bg-surface px-4 py-2 font-mono text-xl tracking-wider">
                {created.initial_password}
              </code>
              <Button variant="secondary" onClick={copy}>
                {copied ? (
                  <Check aria-hidden="true" size={18} />
                ) : (
                  <Copy aria-hidden="true" size={18} />
                )}
                {copied ? "Copied" : "Copy"}
              </Button>
            </div>
            <p className="text-ink-muted">
              Give it to the person privately. Only a secure hash of it is
              stored, so it cannot be shown again.
            </p>
          </div>
          <div>
            <Button variant="quiet" onClick={() => setCreated(null)}>
              Done
            </Button>
          </div>
        </div>
      )}

      <form
        onSubmit={onSubmit}
        noValidate
        className="flex flex-col gap-6 rounded-card border border-line bg-surface p-6 shadow-card sm:p-8"
      >
        <div className="flex items-center gap-3">
          <span
            aria-hidden="true"
            className="grid size-11 place-items-center rounded-xl bg-accent-soft text-accent-hover"
          >
            <UserPlus size={22} />
          </span>
          <h2 className="text-2xl font-bold">Add a user</h2>
        </div>

        {error && <Alert tone="error">{error}</Alert>}

        <fieldset className="flex flex-col gap-2">
          <legend className="mb-2 font-bold">Role</legend>
          <div className="flex flex-wrap gap-3">
            {ROLES.map((r) => (
              <label
                key={r.value}
                className="flex min-h-target cursor-pointer items-center gap-3 rounded-control border-2 border-line-strong px-4 has-checked:border-accent has-checked:bg-accent-soft"
              >
                <input
                  type="radio"
                  name="role"
                  value={r.value}
                  checked={role === r.value}
                  onChange={() => setRole(r.value)}
                  className="size-5 accent-accent"
                />
                <span className="font-bold">{r.label}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <div className="grid gap-6 sm:grid-cols-2">
          <TextField
            label="Full name"
            name="name"
            autoComplete="off"
            required
          />
          <TextField
            label="Email"
            name="email"
            type="email"
            autoComplete="off"
            required
          />
        </div>

        {role === "patient" && (
          <div className="flex flex-col gap-1.5">
            <label htmlFor={clinicianId} className="font-bold">
              Care team clinician
            </label>
            <p className="text-sm text-ink-muted">
              The clinician who will see this patient and set their practice
              limits.
            </p>
            <select
              id={clinicianId}
              name="clinician"
              defaultValue={clinicians[0]?.id ?? ""}
              className="min-h-target rounded-control border-2 border-line-strong bg-surface px-4 text-lg"
            >
              <option value="">No clinician yet</option>
              {clinicians.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        )}

        <div>
          <Button type="submit" busy={busy}>
            <UserPlus aria-hidden="true" size={18} />
            Create account
          </Button>
        </div>
      </form>
    </div>
  );
}
