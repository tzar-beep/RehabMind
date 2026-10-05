import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Browser, type Page } from "@playwright/test";
import { config } from "dotenv";
import path from "node:path";

config({ path: path.resolve(__dirname, "../../.env"), quiet: true });
const PASSWORD = process.env.SEED_DEV_PASSWORD ?? "";

async function signIn(page: Page, email: string) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/clinician$/);
}

// Fail on any browser console error (React key warnings, hydration errors, failed fetches).
test.beforeEach(({ page }) => {
  const errors: string[] = [];
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(e.message));
  (page as Page & { consoleErrors?: string[] }).consoleErrors = errors;
});

test.afterEach(({ page }) => {
  expect((page as Page & { consoleErrors?: string[] }).consoleErrors).toEqual(
    [],
  );
});

async function a11y(page: Page) {
  const r = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(r.violations).toEqual([]);
}

async function openAlex(page: Page): Promise<string> {
  await signIn(page, "clinician@recovery.local");
  const link = page.getByRole("link", { name: "Alex" });
  const href = (await link.getAttribute("href"))!;
  await link.click();
  await expect(page).toHaveURL(href);
  return href;
}

/** Record one real practice answer as the patient, so session views have data. */
async function patientAnswersOnce(browser: Browser) {
  const ctx = await browser.newContext({
    baseURL: "http://localhost:3000",
    extraHTTPHeaders: { Origin: "http://localhost:3000" },
  });
  const login = await ctx.request.post("/api/v1/auth/login", {
    data: { email: "patient@recovery.local", password: PASSWORD },
  });
  expect(login.ok()).toBe(true);
  const state = await (
    await ctx.request.post("/api/v1/practice/sessions")
  ).json();
  await ctx.request.post(
    `/api/v1/practice/exercises/${state.exercise.id}/responses`,
    { data: { skipped: true } },
  );
  await ctx.request.post("/api/v1/practice/sessions/current/end");
  await ctx.close();
}

test("dashboard → patient overview → sessions → session detail", async ({
  page,
  browser,
}) => {
  await patientAnswersOnce(browser);
  await signIn(page, "clinician@recovery.local");
  await expect(
    page.getByRole("heading", { name: "Your patients" }),
  ).toBeVisible();
  await a11y(page);
  await page.screenshot({
    path: "test-results/clinician-dashboard.png",
    fullPage: true,
  });

  await page.getByRole("link", { name: "Alex" }).click();
  await expect(
    page.getByRole("heading", { name: "Current practice limits" }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "Overview" })).toHaveAttribute(
    "aria-current",
    "page",
  );
  await a11y(page);
  await page.screenshot({
    path: "test-results/clinician-overview.png",
    fullPage: true,
  });

  await page.getByRole("link", { name: "Sessions" }).click();
  await expect(
    page.getByRole("heading", { name: "Session history" }),
  ).toBeVisible();
  await a11y(page);
  await page
    .getByRole("table")
    .getByRole("rowheader")
    .first()
    .getByRole("link")
    .click();
  await expect(
    page.getByRole("heading", { name: /^Session on / }),
  ).toBeVisible();
  await expect(page.getByText("No audio is kept")).toBeVisible();
  await a11y(page);
  await page.screenshot({
    path: "test-results/clinician-session.png",
    fullPage: true,
  });
});

test("clinician creates a new practice-limits version (and restores)", async ({
  page,
}) => {
  const href = await openAlex(page);
  await page.goto(`${href}/constraints`);
  const badge = page.getByText(/^Version \d+ · active$/);
  const current = Number((await badge.textContent())!.match(/\d+/)![0]);

  // Invalid values are caught before review (the server would also reject them).
  await page
    .getByRole("button", { name: `Create new version (v${current + 1})` })
    .click();
  await page.getByLabel("Exercises per session").fill("99");
  await page.getByRole("button", { name: "Review changes" }).click();
  await expect(
    page.getByText("Enter a whole number from 1 to 50."),
  ).toBeVisible();
  await page.getByRole("button", { name: "Cancel" }).click();

  const original = (await page
    .locator("dt", { hasText: "Exercises per session" })
    .first()
    .locator("xpath=following-sibling::dd[1]")
    .textContent())!;

  async function createVersion(size: string, expected: number) {
    await page
      .getByRole("button", { name: `Create new version (v${expected})` })
      .click();
    await page.getByLabel("Exercises per session").fill(size);
    await page.getByRole("button", { name: "Review changes" }).click();
    await expect(
      page.getByRole("heading", { name: `Review version ${expected}` }),
    ).toBeFocused();
    await expect(page.getByText("(changed)")).toBeVisible();
    await a11y(page);
    await page
      .getByRole("button", { name: `Save as version ${expected}` })
      .click();
    await expect(
      page.getByText(`Version ${expected} created and now active`),
    ).toBeVisible();
    await expect(page.getByText(`Version ${expected} · active`)).toBeVisible();
  }

  await createVersion(original === "6" ? "7" : "6", current + 1);
  // The previous version stays in the read-only history.
  await expect(
    page.getByRole("listitem").filter({ hasText: `Version ${current}` }),
  ).toContainText("Superseded");
  await page.screenshot({
    path: "test-results/clinician-constraints.png",
    fullPage: true,
  });
  await createVersion(original, current + 2); // restore dev data
});

test("AI audit log explains accepted, retried and rule-based exercises", async ({
  page,
}) => {
  const href = await openAlex(page);
  await page.goto(`${href}/ai-generations`);
  await expect(
    page.getByRole("heading", { name: "AI audit log" }),
  ).toBeVisible();
  await expect(
    page.getByText("This is audit metadata recorded by the application.", {
      exact: false,
    }),
  ).toBeVisible();
  const entries = page.locator("details > summary");
  if ((await entries.count()) > 0) {
    await entries.first().click();
    await expect(
      page.getByRole("table", { name: "Attempts and validation" }).first(),
    ).toBeVisible();
  }
  await a11y(page);
  await page.screenshot({
    path: "test-results/clinician-ai-log.png",
    fullPage: true,
  });
});

test("another care team's clinician cannot open the patient", async ({
  page,
}) => {
  const href = await openAlex(page);
  const patientId = href.split("/").pop()!;
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/login$/);

  await signIn(page, "clinician2@recovery.local");
  await expect(page.getByRole("link", { name: "Sam" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Alex" })).toHaveCount(0);
  for (const suffix of ["", "/sessions", "/constraints", "/ai-generations"]) {
    await page.goto(`${href}${suffix}`);
    await expect(
      page.getByRole("heading", { name: "Patient not available" }),
    ).toBeVisible();
  }
  for (const api of [
    "overview",
    "sessions",
    "constraints/versions",
    "ai-generations/runs",
  ]) {
    const r = await page.request.get(`/api/v1/patients/${patientId}/${api}`);
    expect(r.status(), api).toBe(404);
  }
  const post = await page.request.post(
    `/api/v1/patients/${patientId}/constraints`,
    {
      headers: { Origin: "http://localhost:3000" },
      data: {
        allowed_exercise_types: ["picture_naming"],
        allowed_response_modes: ["text"],
        min_difficulty: 1,
        max_difficulty: 5,
        max_exercises_per_session: 8,
      },
    },
  );
  expect(post.status()).toBe(404);
});
