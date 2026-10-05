import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { config } from "dotenv";
import path from "node:path";

config({ path: path.resolve(__dirname, "../../.env"), quiet: true });
const PASSWORD = process.env.SEED_DEV_PASSWORD ?? "";

async function signIn(page: Page, email: string, password = PASSWORD) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
}

async function expectNoA11yViolations(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
}

test.beforeAll(() => {
  expect(
    PASSWORD,
    "SEED_DEV_PASSWORD missing; run the dev seed first",
  ).not.toBe("");
});

test("login page is accessible and shows a clear error for bad credentials", async ({
  page,
}) => {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await expectNoA11yViolations(page);

  await signIn(page, "nobody@recovery.local", "wrong-password");
  await expect(
    page.getByText("Email or password is incorrect."),
  ).toHaveAttribute("role", "alert");
  await expect(page).toHaveURL(/\/login$/);
});

test("patient signs in, sees their home, and signs out", async ({
  page,
  context,
}) => {
  await signIn(page, "patient@recovery.local");
  await expect(page).toHaveURL(/\/patient$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Hello, Alex",
  );
  await expectNoA11yViolations(page);

  const session = (await context.cookies()).find(
    (c) => c.name === "sra_session",
  );
  expect(session?.httpOnly).toBe(true);
  expect(session?.sameSite).toBe("Lax");

  await page.goto("/admin");
  await expect(page).toHaveURL(/\/patient$/);

  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await page.goto("/patient");
  await expect(page).toHaveURL(/\/login$/);
});

test("clinician sees only assigned patients", async ({ page }) => {
  await signIn(page, "clinician@recovery.local");
  await expect(page).toHaveURL(/\/clinician$/);
  const rows = page.getByRole("table").getByRole("row");
  await expect(rows).toHaveCount(2); // header + one assigned patient
  await expect(page.getByRole("link", { name: "Alex" })).toBeVisible();
  await expect(page.getByText("Sam")).toHaveCount(0); // another care team
  await expectNoA11yViolations(page);
});

test("admin sees accounts without clinical data", async ({ page }) => {
  await signIn(page, "admin@recovery.local");
  await expect(page).toHaveURL(/\/admin$/);
  await expect(page.getByRole("heading", { name: "Accounts" })).toBeVisible();
  await expectNoA11yViolations(page);
  await page.goto("/clinician");
  await expect(page).toHaveURL(/\/admin$/);
});

test("keyboard users can skip to main content", async ({ page }) => {
  await signIn(page, "patient@recovery.local");
  await expect(page).toHaveURL(/\/patient$/);
  await page.goto("/patient"); // fresh document: focus starts at the top
  await page.keyboard.press("Tab");
  const skip = page.getByRole("link", { name: "Skip to main content" });
  await expect(skip).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main")).toBeFocused();
});
