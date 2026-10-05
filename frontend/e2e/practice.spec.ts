import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { config } from "dotenv";
import path from "node:path";

config({ path: path.resolve(__dirname, "../../.env"), quiet: true });

async function a11y(page: Page) {
  const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  expect(r.violations).toEqual([]);
}

test("patient practises picture naming end to end", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill("patient@recovery.local");
  await page.getByLabel("Password").fill(process.env.SEED_DEV_PASSWORD ?? "");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/patient$/);

  await page.getByRole("link", { name: /(Start|Continue) practice/ }).click();
  await expect(page.getByRole("heading", { name: "What is this?" })).toBeVisible();
  await expect(page.getByRole("img", { name: "Picture to name" })).toBeVisible();
  await expect(page.getByLabel("Your answer")).toBeFocused();
  await a11y(page);
  await page.screenshot({ path: "test-results/practice-question.png", fullPage: true });

  // Empty submit gives an accessible inline error, not a request.
  await page.getByRole("button", { name: "Check" }).click();
  await expect(page.getByText("Type a word, or choose")).toBeVisible();

  await page.getByLabel("Your answer").fill("zzzz");
  await page.getByRole("button", { name: "Check" }).click();
  await expect(page.getByText("Good try.")).toBeVisible();
  await expect(page.getByText("The word is")).toBeVisible();
  const next = page.getByRole("button", { name: /Next picture|See how you did/ });
  await expect(next).toBeFocused();
  await a11y(page);
  await page.screenshot({ path: "test-results/practice-feedback.png", fullPage: true });
  await next.click();

  await page.getByRole("button", { name: "I’m not sure" }).click();
  await expect(page.getByText("That's okay.")).toBeVisible();
  await page.getByRole("button", { name: /Next picture|See how you did/ }).click();

  await page.getByRole("button", { name: "Stop for today" }).click();
  await expect(page).toHaveURL(/\/patient$/);
  await expect(page.getByRole("link", { name: "Start practice" })).toBeVisible();
});
