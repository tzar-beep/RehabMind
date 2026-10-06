"use client";

import { useRouter } from "next/navigation";
import { useRef, useState, type FormEvent } from "react";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { PasswordField } from "@/components/ui/PasswordField";
import { TextField } from "@/components/ui/TextField";
import { ApiError, apiFetch } from "@/lib/api/client";
import { MeSchema, ROLE_HOME } from "@/lib/api/schemas";

export function LoginForm() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const emailRef = useRef<HTMLInputElement>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");
    if (!email || !password) {
      setError("Please enter your email and password.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const me = await apiFetch(
        "/auth/login",
        { method: "POST", json: { email, password } },
        MeSchema,
      );
      router.replace(ROLE_HOME[me!.role]);
      router.refresh();
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.message
          : "Something went wrong. Please try again.",
      );
      setBusy(false);
      emailRef.current?.focus();
    }
  }

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-6">
      {error && <Alert tone="error">{error}</Alert>}
      <TextField
        ref={emailRef}
        label="Email"
        name="email"
        type="email"
        autoComplete="username"
        inputMode="email"
        required
      />
      <PasswordField
        label="Password"
        name="password"
        autoComplete="current-password"
        required
      />
      <Button type="submit" size="lg" busy={busy}>
        {busy ? "Signing in…" : "Sign in"}
      </Button>
    </form>
  );
}
