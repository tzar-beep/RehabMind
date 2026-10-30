import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { apiFetch, markSigningOut } from "./client";

describe("apiFetch on a 401", () => {
  const assign = vi.fn();

  beforeEach(async () => {
    assign.mockClear();
    vi.stubGlobal("location", { assign });
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("{}", { status: 401 })),
    );
    await apiFetch("/auth/login", { method: "POST" }).catch(() => undefined);
  });
  afterEach(() => vi.unstubAllGlobals());

  it("explains an expired session", async () => {
    await expect(apiFetch("/practice/mood")).rejects.toThrow();
    expect(assign).toHaveBeenCalledWith("/login?expired=1");
  });

  it("does not call a request cut off by signing out an expiry", async () => {
    markSigningOut();
    await expect(apiFetch("/practice/mood")).rejects.toThrow();
    expect(assign).not.toHaveBeenCalled();
  });

  it("explains an expiry again after the next sign-in", async () => {
    markSigningOut();
    await apiFetch("/auth/login", { method: "POST" }).catch(() => undefined);
    await expect(apiFetch("/practice/mood")).rejects.toThrow();
    expect(assign).toHaveBeenCalledWith("/login?expired=1");
  });
});
