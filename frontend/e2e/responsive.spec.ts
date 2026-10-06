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

/** No horizontal page scroll; every visible control at least 44px in each direction. */
async function layoutChecks(page: Page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
  const small = await page.evaluate(() =>
    [...document.querySelectorAll("button, input, select, textarea, a[href]")]
      .filter((el) => {
        const r = el.getBoundingClientRect();
        const style = getComputedStyle(el);
        // Inline text links inside sentences are exempt (WCAG 2.5.8 inline exception).
        const inline = el.tagName === "A" && style.display === "inline";
        // Visually hidden until focused (skip link) is exempt while hidden.
        const hidden = el.matches(".sr-only:not(:focus)");
        return !hidden && !inline && (r.height < 44 || r.width < 44);
      })
      .map((el) => el.outerHTML.slice(0, 80)),
  );
  expect(small).toEqual([]);
  const r = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(r.violations).toEqual([]);
}

test.describe("phone (375px)", () => {
  test.use({ viewport: { width: 375, height: 812 } });

  test("patient login, home and practice fit and stay accessible", async ({
    page,
  }) => {
    await page.goto("/login");
    await layoutChecks(page);
    await signIn(page, "patient@recovery.local");
    await expect(page).toHaveURL(/\/patient$/);
    await layoutChecks(page);
    await page.getByRole("link", { name: /(Start|Continue) practice/ }).click();
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await layoutChecks(page);
    await page.getByRole("button", { name: "Stop for today" }).click();
    await expect(page).toHaveURL(/\/patient$/);
  });
});

test.describe("tablet (768px)", () => {
  test.use({ viewport: { width: 768, height: 1024 } });

  test("clinician dashboard and patient overview fit", async ({ page }) => {
    await signIn(page, "clinician@recovery.local");
    await expect(page).toHaveURL(/\/clinician$/);
    await layoutChecks(page);
    await page.getByRole("link", { name: "Alex" }).click();
    await expect(
      page.getByRole("heading", { name: "Current practice limits" }),
    ).toBeVisible();
    await layoutChecks(page);
  });
});

test.describe("reduced motion", () => {
  test.use({ reducedMotion: "reduce" });

  test("animations are effectively disabled", async ({ page }) => {
    await page.goto("/login");
    const duration = await page.evaluate(
      () => getComputedStyle(document.body).transitionDuration,
    );
    expect(Number.parseFloat(duration)).toBeLessThanOrEqual(0.001);
  });
});
