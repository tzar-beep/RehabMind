import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { config } from "dotenv";
import path from "node:path";

config({ path: path.resolve(__dirname, "../../.env"), quiet: true });

test("talk board speaks a phrase and can show it big", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill("patient@recovery.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.SEED_DEV_PASSWORD ?? "");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/patient$/);
  await page.getByRole("link", { name: "Talk", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Talk" })).toBeVisible();

  await page.getByRole("tab", { name: "Answers" }).click();
  await page.getByRole("button", { name: "Yes", exact: true }).click();
  await expect(page.getByText("Yes.", { exact: true })).toBeVisible();

  const axe = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(axe.violations).toEqual([]);

  await page.getByRole("button", { name: "Show big" }).click();
  const big = page.getByRole("dialog", { name: "Shown big" });
  await expect(big).toContainText("Yes.");
  await big.getByRole("button", { name: "Close" }).click();
  await expect(big).toBeHidden();
});

test("everyday phrases: a script line by line, then a summary", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill("patient@recovery.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.SEED_DEV_PASSWORD ?? "");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/patient$/);
  await page.getByRole("link", { name: "Phrases" }).click();
  await page.getByRole("button", { name: /On the phone/ }).click();
  for (let i = 0; i < 4; i++) {
    await page.getByRole("button", { name: "Say it together" }).click();
    await page.getByRole("button", { name: "My turn" }).click();
    await page.getByRole("button", { name: "I said it" }).click();
  }
  await expect(
    page.getByRole("heading", { name: "On the phone: done" }),
  ).toBeVisible();
  await expect(page.getByText("You said 4 of 4 lines.")).toBeVisible();
  const axe = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(axe.violations).toEqual([]);
});
