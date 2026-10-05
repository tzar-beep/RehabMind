import "server-only";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { z } from "zod";

import { MeSchema, ROLE_HOME, type Me, type Role } from "./schemas";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

/** Server-side GET to the backend, forwarding the user's session cookie. */
export async function backendGet<T extends z.ZodType>(
  path: string,
  schema: T,
): Promise<z.infer<T> | null> {
  const cookieHeader = (await cookies()).toString();
  const res = await fetch(`${BACKEND_URL}/api/v1${path}`, {
    headers: cookieHeader ? { cookie: cookieHeader } : {},
    cache: "no-store",
  });
  if (res.status === 401 || res.status === 403 || res.status === 404)
    return null;
  if (!res.ok) throw new Error(`Backend request failed: ${res.status}`);
  return schema.parse(await res.json());
}

export function getCurrentUser(): Promise<Me | null> {
  return backendGet("/auth/me", MeSchema);
}

/**
 * Gate a route to one role. This is a navigation convenience only:
 * the backend enforces authorization on every request.
 */
export async function requireRole(role: Role): Promise<Me> {
  const me = await getCurrentUser();
  if (!me) redirect("/login");
  if (me.role !== role) redirect(ROLE_HOME[me.role]);
  return me;
}
