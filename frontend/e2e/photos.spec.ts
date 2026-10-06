import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { config } from "dotenv";
import path from "node:path";

config({ path: path.resolve(__dirname, "../../.env"), quiet: true });
const PASSWORD = process.env.SEED_DEV_PASSWORD ?? "";
const ORIGIN = { Origin: "http://localhost:3000" };

/** As the clinician, enable the photo exercises for Alex (new constraint version). */
async function enablePhotoExercises(page: Page, sentenceOnly = false) {
  const login = await page.request.post("/api/v1/auth/login", {
    headers: ORIGIN,
    data: { email: "clinician@recovery.local", password: PASSWORD },
  });
  expect(login.ok()).toBe(true);
  const patients = await (
    await page.request.get("/api/v1/clinicians/me/patients")
  ).json();
  const alex = patients.find(
    (p: { display_name: string }) => p.display_name === "Alex",
  );
  const r = await page.request.post(`/api/v1/patients/${alex.id}/constraints`, {
    headers: ORIGIN,
    data: {
      allowed_exercise_types: sentenceOnly
        ? ["sentence_construction"]
        : ["picture_naming", "picture_description", "sentence_construction"],
      allowed_response_modes: ["text", "speech"],
      min_difficulty: 1,
      max_difficulty: 3,
      max_exercises_per_session: sentenceOnly ? 1 : 8,
    },
  });
  expect(r.status()).toBe(201);
  await page.request.post("/api/v1/auth/logout", { headers: ORIGIN });
}

test("patient builds a sentence from a real-world photo", async ({ page }) => {
  await enablePhotoExercises(page, true);
  await page.goto("/login");
  await page.getByLabel("Email").fill("patient@recovery.local");
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/patient$/);
  await page.request.post("/api/v1/practice/sessions/current/end", {
    headers: ORIGIN,
  });
  await page.goto("/patient/practice");

  const photo = page.getByRole("img", { name: "Picture for the sentence" });
  await expect(photo).toBeVisible();
  await expect(photo).toHaveAttribute("src", /^\/stimuli\/photos\/.+\.jpg$/);
  await expect(page.getByRole("button", { name: "Check" })).toBeVisible();
  await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze()
    .then((r) => expect(r.violations).toEqual([]));

  // Tap every word (bank order is scrambled, so this is usually wrong) and check.
  const adds = page.getByRole("button", { name: /^Add / });
  while ((await adds.count()) > 0) await adds.first().click();
  await page.getByRole("button", { name: "Check" }).click();
  await expect(page.getByText(/You built it|The sentence is/)).toBeVisible();
  await page.screenshot({
    path: "test-results/photo-sentence.png",
    fullPage: true,
  });

  await page.getByRole("button", { name: "See how you did" }).click();
  await expect(
    page.getByRole("heading", { name: "Practice complete" }),
  ).toBeVisible();

  // Restore the broader dev plan for other tests and demos.
  await enablePhotoExercises(page);
});
