import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { config } from "dotenv";
import path from "node:path";

config({ path: path.resolve(__dirname, "../../.env"), quiet: true });

// A tiny valid PNG (the backend re-encodes every photo).
const PHOTO = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "base64",
);

test("family member sees practice and adds a word from the patient's life", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill("carer@recovery.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.SEED_DEV_PASSWORD ?? "");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/carer$/);
  await expect(
    page.getByRole("heading", { name: "How Alex is getting on" }),
  ).toBeVisible();
  // Activity and goals only: no scores.
  await expect(page.getByText(/correct/i)).toHaveCount(0);

  await page.locator('input[type="file"]').setInputFiles({
    name: "rex.png",
    mimeType: "image/png",
    buffer: PHOTO,
  });
  await page.getByLabel("The word to practise").fill("Rex");
  await page.getByRole("button", { name: "Add word" }).click();
  await expect(page.getByText("“Rex” was added.")).toBeVisible();
  const card = page.getByRole("listitem").filter({ hasText: "Rex" });
  await expect(card).toBeVisible();
  // The private photo loads for the family member.
  await expect
    .poll(() =>
      card.locator("img").evaluate((i: HTMLImageElement) => i.naturalWidth),
    )
    .toBeGreaterThan(0);

  const axe = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(axe.violations).toEqual([]);

  await card.getByRole("button", { name: "Remove Rex" }).click();
  await expect(card).toHaveCount(0);
});
