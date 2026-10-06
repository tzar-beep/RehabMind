import type { z } from "zod";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

const FALLBACK_MESSAGE = "Something went wrong. Please try again.";

/** Browser-side call to the same-origin API. Cookies are sent automatically. */
export async function apiFetch<T extends z.ZodType>(
  path: string,
  init: RequestInit & { json?: unknown } = {},
  schema?: T,
): Promise<z.infer<T> | undefined> {
  const { json, ...rest } = init;
  let res: Response;
  try {
    res = await fetch(`/api/v1${path}`, {
      ...rest,
      credentials: "same-origin",
      headers:
        json === undefined
          ? rest.headers
          : { "Content-Type": "application/json" },
      body: json === undefined ? rest.body : JSON.stringify(json),
    });
  } catch {
    throw new ApiError(
      0,
      "We couldn't reach the server. Check your connection and try again.",
    );
  }
  if (res.status === 401 && path !== "/auth/login") {
    // Session expired (30 min idle or 12 h): back to sign-in, with an explanation.
    // A full page load on purpose: it drops all in-memory state of the expired session.
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.assign("/login?expired=1");
  }
  if (!res.ok) {
    const detail = await res.json().then(
      (b) => b?.detail,
      () => undefined,
    );
    throw new ApiError(
      res.status,
      typeof detail === "string" ? detail : FALLBACK_MESSAGE,
    );
  }
  if (!schema || res.status === 204) return undefined;
  return schema.parse(await res.json());
}
