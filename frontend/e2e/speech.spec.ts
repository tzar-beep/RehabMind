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
  await page.getByLabel("Password").fill(process.env.SEED_DEV_PASSWORD ?? "");
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.getByRole("link", { name: /(Start|Continue) practice/ }).click();

  await expect(page.getByText("Say the word for this picture.")).toBeVisible();
  await page.getByRole("button", { name: "Start speaking" }).click();
  await expect(page.getByText(/Listening…/)).toBeVisible();
  await page.waitForTimeout(2_500);
  await page.getByRole("button", { name: "Stop recording" }).click();
  await expect(page.getByText("Checking your answer…")).toBeVisible();

  if (process.env.E2E_FAKE_AUDIO) {
    // Synthetic speech: a transcript is produced and the exercise is scored.
    await expect(page.getByText(/The word is|You named it/)).toBeVisible({
      timeout: 60_000,
    });
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
