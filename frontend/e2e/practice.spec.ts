import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { config } from "dotenv";
import path from "node:path";

config({ path: path.resolve(__dirname, "../../.env"), quiet: true });

// Each test starts a fresh session, whatever was left open in the dev database.
async function endOpenSession(page: Page) {
  const r = await page.request.post("/api/v1/practice/sessions/current/end", {
    headers: { Origin: new URL(page.url()).origin },
  });
  expect(r.ok()).toBe(true);
}

async function a11y(page: Page) {
  const r = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(r.violations).toEqual([]);
}

test("patient practises picture naming end to end", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill("patient@recovery.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.SEED_DEV_PASSWORD ?? "");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/patient$/);
  await endOpenSession(page);
  await page.reload();

  await page.getByRole("link", { name: /(Start|Continue) practice/ }).click();
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(
    page.getByRole("img", { name: "Picture to name" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Type instead" }).click();
  await expect(page.getByLabel("Your answer")).toBeFocused();
  await a11y(page);
  await page.screenshot({
    path: "test-results/practice-question.png",
    fullPage: true,
  });

  // Empty submit gives an accessible inline error, not a request.
  await page.getByRole("button", { name: "Check" }).click();
  await expect(page.getByText("Type a word, or choose")).toBeVisible();

  await page.getByLabel("Your answer").fill("zzzz");
  await page.getByRole("button", { name: "Check" }).click();
  await expect(page.getByText("Good try.")).toBeVisible();
  await expect(page.getByText("The word is")).toBeVisible();
  const next = page.getByRole("button", {
    name: /Next picture|See how you did/,
  });
  await expect(next).toBeFocused();
  // The AI tip loads after the standard feedback; it may or may not appear (validation
  // can reject it), but the screen must settle and stay accessible either way.
  await expect(page.getByText("Preparing a tip for you…")).toBeHidden({
    timeout: 60_000,
  });
  await a11y(page);
  await page.screenshot({
    path: "test-results/practice-feedback.png",
    fullPage: true,
  });
  await next.click();

  await page.getByRole("button", { name: "I’m not sure" }).click();
  await expect(page.getByText("That's okay.")).toBeVisible();
  await page
    .getByRole("button", { name: /Next picture|See how you did/ })
    .click();

  await page.getByRole("button", { name: "Stop for today" }).click();
  await expect(page).toHaveURL(/\/patient$/);
  await expect(
    page.getByRole("link", { name: "Start practice" }),
  ).toBeVisible();
});

test("hints reveal meaning first, then the first sound", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill("patient@recovery.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.SEED_DEV_PASSWORD ?? "");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/patient$/);
  await endOpenSession(page);
  await page.reload();
  await page.getByRole("link", { name: /(Start|Continue) practice/ }).click();
  await page.getByRole("button", { name: "Show a hint" }).click();
  await expect(page.getByRole("listitem")).toHaveCount(1);
  await page.getByRole("button", { name: "Show another hint" }).click();
  await expect(page.getByText(/^It starts with “.+…”$/)).toBeVisible();
  await expect(
    page.getByRole("button", { name: /Show (a|another) hint/ }),
  ).toHaveCount(0);
  await a11y(page);
  await page.screenshot({
    path: "test-results/practice-hints.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Stop for today" }).click();
  await expect(page).toHaveURL(/\/patient$/);
});

test("sentence building can switch to speaking and back", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill("patient@recovery.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.SEED_DEV_PASSWORD ?? "");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/patient$/);
  await endOpenSession(page);
  await page.reload();
  await page.getByRole("link", { name: /(Start|Continue) practice/ }).click();
  await expect(
    page.getByRole("button", { name: "Stop for today" }),
  ).toBeVisible();

  // Exercise types rotate within a session; skip ahead to a sentence exercise.
  const words = page.getByRole("region", { name: "Words", exact: true });
  const speakInstead = page.getByRole("button", { name: "Speak instead" });
  for (let i = 0; i < 8 && !(await words.isVisible()); i++) {
    if (await speakInstead.isVisible()) await speakInstead.click();
    await page.getByRole("button", { name: "I’m not sure" }).click();
    await page
      .getByRole("button", { name: /Next picture|See how you did/ })
      .click();
    if (
      await page.getByRole("heading", { name: "Practice complete" }).isVisible()
    )
      await page.goto("/patient/practice");
  }
  await expect(words).toBeVisible();

  await speakInstead.click();
  await expect(
    page.getByRole("button", { name: "Start speaking" }),
  ).toBeVisible();
  await expect(words).toBeHidden();
  await page.getByRole("button", { name: "Tap words instead" }).click();
  await expect(words).toBeVisible();

  await page.getByRole("button", { name: "Stop for today" }).click();
  await expect(page).toHaveURL(/\/patient$/);
});
