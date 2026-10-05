import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { ROLE_HOME } from "@/lib/api/schemas";
import { getCurrentUser } from "@/lib/api/server";

import { LoginForm } from "./LoginForm";

export const metadata: Metadata = { title: "Sign in" };

export default async function LoginPage() {
  const me = await getCurrentUser();
  if (me) redirect(ROLE_HOME[me.role]);

  return (
    <main
      id="main"
      className="flex flex-1 items-center justify-center px-6 py-12"
    >
      <div className="w-full max-w-md">
        <p className="mb-8 text-center text-lg font-bold">
          <span aria-hidden="true" className="mr-2 text-accent">
            ●
          </span>
          RehabMind
        </p>
        <div className="rounded-card border border-line bg-surface p-8 shadow-sm">
          <h1 className="mb-2 text-3xl font-bold">Sign in</h1>
          <p className="mb-8 text-ink-muted">Welcome back. Take your time.</p>
          <LoginForm />
        </div>
      </div>
    </main>
  );
}
