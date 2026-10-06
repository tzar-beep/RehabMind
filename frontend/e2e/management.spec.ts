import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { config } from "dotenv";
import path from "node:path";

config({ path: path.resolve(__dirname, "../../.env"), quiet: true });
const PASSWORD = process.env.SEED_DEV_PASSWORD ?? "";

async function signIn(page: Page, email: string) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
}

async function a11y(page: Page) {
  const r = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(r.violations).toEqual([]);
}

// These checks open the forms but never submit them, so dev data is left untouched.

test("admin add-user form is accessible and shows the clinician picker for patients", async ({
  page,
}) => {
  await signIn(page, "admin@recovery.local");
  await expect(page).toHaveURL(/\/admin$/);
  await expect(page.getByRole("heading", { name: "Add a user" })).toBeVisible();
  await expect(page.getByLabel("Care team clinician")).toBeVisible();
  await page.getByRole("radio", { name: "Clinician" }).check();
  await expect(page.getByLabel("Care team clinician")).toHaveCount(0);
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(
    page.getByText("Please enter a name and an email"),
  ).toBeVisible();
  await a11y(page);
});

test("clinician reset dialog explains the fresh start and needs a reason", async ({
  page,
}) => {
  await signIn(page, "clinician@recovery.local");
  await expect(page).toHaveURL(/\/clinician$/);
  await page.getByRole("link", { name: "Alex" }).click();
  await page.getByRole("button", { name: "Reset progress…" }).click();
  const dialog = page.getByRole("dialog", { name: /fresh start/ });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByText("What is kept")).toBeVisible();
  await dialog.getByRole("button", { name: "Reset progress" }).click();
  await expect(dialog.getByText("Please give a short reason")).toBeVisible();
  await a11y(page);
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
});

test("AI pipeline demo view renders without errors when enabled", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(e.message));
  await signIn(page, "clinician@recovery.local");
  await expect(page).toHaveURL(/\/clinician$/);
  await page.getByRole("link", { name: "Alex" }).click();
  const tab = page.getByRole("link", { name: "AI pipeline (demo)" });
  await expect(page.getByRole("link", { name: "Overview" })).toBeVisible();
  test.skip(!(await tab.isVisible()), "AI_DEMO_VIEW is off");
  await tab.click();
  await expect(
    page.getByRole("heading", {
      name: "Patient performance: learned ability model",
    }),
  ).toBeVisible();
  await a11y(page);
  expect(errors).toEqual([]);
});
