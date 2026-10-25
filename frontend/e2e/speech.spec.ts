import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { config } from "dotenv";
import path from "node:path";

config({ path: path.resolve(__dirname, "../../.env"), quiet: true });

test("patient answers by voice through the real speech pipeline", async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.goto("/login");
  await page.getByLabel("Email").fill("patient@recovery.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.SEED_DEV_PASSWORD ?? "");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/patient$/);
  // Start from a fresh session (the first exercise is picture naming).
  const end = await page.request.post("/api/v1/practice/sessions/current/end", {
    headers: { Origin: new URL(page.url()).origin },
  });
  expect(end.ok()).toBe(true);
  await page.reload();
  await page
    .getByRole("link", { name: /(Start|Start new|Continue) practice/ })
    .click();

  await expect(page.getByText("Say the word for this picture.")).toBeVisible();
  await page.getByRole("button", { name: "Start speaking" }).click();
  await expect(page.getByText(/Listening…/)).toBeVisible();
  await page.waitForTimeout(2_500);
  await page.getByRole("button", { name: "Stop recording" }).click();
  await expect(page.getByText("Checking your answer…")).toBeVisible();

  if (process.env.E2E_FAKE_AUDIO) {
    // Synthetic speech: a transcript is produced and the exercise is scored. A match
    // first asks the patient to confirm what was heard.
    const yes = page.getByRole("button", { name: "Yes" });
    const feedback = page.getByText(/The word is|You named it/);
    await expect(yes.or(feedback)).toBeVisible({ timeout: 60_000 });
    if (await yes.isVisible()) await yes.click();
    await expect(feedback).toBeVisible();
    await page.screenshot({
      path: "test-results/speech-feedback.png",
      fullPage: true,
    });
  } else {
    // Fake-device test tone: no speech detected, exercise stays open, typing remains possible.
    await expect(
      page.getByText("I didn’t catch that.", { exact: false }),
    ).toBeVisible({
      timeout: 60_000,
    });
    await page.getByRole("button", { name: "Type instead" }).click();
    await expect(page.getByLabel("Your answer")).toBeVisible();
  }

  await page.goto("/patient/practice");
  await page.getByRole("button", { name: "Stop for today" }).click();
  await expect(page).toHaveURL(/\/patient$/);
});

test("patient is asked to confirm a recognised match, and can say no", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill("patient@recovery.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.SEED_DEV_PASSWORD ?? "");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/patient$/);
  const end = await page.request.post("/api/v1/practice/sessions/current/end", {
    headers: { Origin: new URL(page.url()).origin },
  });
  expect(end.ok()).toBe(true);
  await page.reload();
  // The recogniser's answer is mocked: this checks the screen, not speech recognition
  // (the backend flow is covered by tests/test_speech.py).
  await page.route("**/api/v1/practice/exercises/*/speech", (r) =>
    r.fulfill({ status: 202, json: { recording_id: "rec-1" } }),
  );
  await page.route("**/api/v1/practice/speech/rec-1", (r) =>
    r.fulfill({ json: { status: "confirm", heard: "door", result: null } }),
  );
  await page.route("**/api/v1/practice/speech/rec-1/confirm", (r) =>
    r.fulfill({ json: { status: "rejected", heard: null, result: null } }),
  );
  await page
    .getByRole("link", { name: /(Start|Start new|Continue) practice/ })
    .click();
  await page.getByRole("button", { name: "Start speaking" }).click();
  await page.waitForTimeout(1_000);
  await page.getByRole("button", { name: "Stop recording" }).click();

  const question = page.getByRole("group", { name: /Is that what you said/ });
  await expect(question).toContainText("“door”");
  const axe = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(axe.violations).toEqual([]);
  await page.screenshot({ path: "test-results/speech-confirm.png" });
  await page.getByRole("button", { name: "No, try again" }).click();
  await expect(page.getByText("Thanks for telling me.")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Start speaking" }),
  ).toBeVisible();

  await page.unrouteAll();
  await page.getByRole("button", { name: "Stop for today" }).click();
  await expect(page).toHaveURL(/\/patient$/);
});
