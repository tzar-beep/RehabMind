import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { config } from "dotenv";
import path from "node:path";

config({ path: path.resolve(__dirname, "../../.env"), quiet: true });

// Phase 2 part A (docs/validation/protocols/phase2-older-adults.md): the usability tasks, in
// order, on a phone and a laptop. People's ease of use (SUS) needs participants; this checks
// that every task can be done, in few steps, with large targets and no accessibility errors.

const VIEWPORTS = [
  { name: "phone", width: 390, height: 844 },
  { name: "laptop", width: 1280, height: 800 },
];
// WCAG 2.5.5 (AAA) target size; aphasia often comes with right-hand weakness after stroke.
const MIN_TARGET = 44;

async function a11y(page: Page) {
  const r = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(r.violations).toEqual([]);
}

async function bigTargets(page: Page) {
  const small = await page
    .locator("main button:visible, main a:visible")
    .evaluateAll(
      (els, min) =>
        els
          .map((e) => ({
            text: e.textContent?.trim(),
            r: e.getBoundingClientRect(),
          }))
          .filter(({ r }) => r.width > 0 && Math.min(r.width, r.height) < min)
          .map(
            ({ text, r }) =>
              `${text} (${Math.round(r.width)}×${Math.round(r.height)})`,
          ),
      MIN_TARGET,
    );
  expect(small).toEqual([]);
}

/** Counts the user's actions per task, so a task that needs too many steps fails. */
function steps(page: Page) {
  let n = 0;
  return {
    click: async (
      name: string | RegExp,
      role: "button" | "link" = "button",
    ) => {
      n++;
      await page.getByRole(role, { name }).first().click();
    },
    type: async (text: string) => {
      n++;
      await page.getByRole("textbox").first().fill(text);
    },
    done: (budget: number) => {
      expect(n).toBeLessThanOrEqual(budget);
      n = 0;
    },
  };
}

for (const vp of VIEWPORTS) {
  test(`usability tasks on a ${vp.name}`, async ({ page }) => {
    test.setTimeout(180_000);
    await page.setViewportSize({ width: vp.width, height: vp.height });
    const user = steps(page);

    // 1. Sign in.
    await page.goto("/login");
    await page.getByLabel("Email").fill("patient@recovery.local");
    await page
      .getByLabel("Password", { exact: true })
      .fill(process.env.SEED_DEV_PASSWORD ?? "");
    await user.click("Sign in");
    await expect(page).toHaveURL(/\/patient$/);
    user.done(1);
    await page.request.post("/api/v1/practice/sessions/current/end", {
      headers: { Origin: new URL(page.url()).origin },
    });
    await page.reload();
    await a11y(page);
    await bigTargets(page);

    // 2. Start practice.
    await user.click(/(Start|Continue) practice/, "link");
    await expect(
      page.getByRole("button", { name: "I’m not sure" }).first(),
    ).toBeVisible();
    user.done(1);
    await a11y(page);
    await bigTargets(page);

    // 3. Use a hint.
    const hint = page.getByRole("button", { name: /Show (a|another) hint/ });
    if (await hint.isVisible()) {
      await user.click(/Show (a|another) hint/);
      user.done(1);
    }

    // 4. Answer three pictures: type where there is a box, otherwise "I'm not sure".
    for (let i = 0; i < 3; i++) {
      const typeInstead = page.getByRole("button", { name: "Type instead" });
      if (await typeInstead.isVisible()) await user.click("Type instead");
      if (await page.getByRole("textbox").first().isVisible()) {
        await user.type("cup");
        await user.click("Check");
      } else {
        await user.click("I’m not sure");
      }
      await expect(
        page.getByRole("button", { name: /Next picture|See how you did/ }),
      ).toBeVisible();
      await bigTargets(page);
      await user.click(/Next picture|See how you did/);
      user.done(4); // switch mode, type, check, next
      await expect(
        page
          .getByRole("button", { name: "I’m not sure" })
          .first()
          .or(page.getByRole("heading", { name: "Practice complete" })),
      ).toBeVisible();
    }

    // 5. Stop early ("Stop for today" ends the session), then come back and start again.
    await user.click("Stop for today");
    await expect(page).toHaveURL(/\/patient$/);
    await user.click(/(Start|Continue) practice/, "link");
    await expect(
      page.getByRole("button", { name: "I’m not sure" }).first(),
    ).toBeVisible();
    user.done(2);

    // 6. Finish and give the difficulty rating.
    for (let i = 0; i < 20; i++) {
      if (
        await page
          .getByRole("heading", { name: "Practice complete" })
          .isVisible()
      )
        break;
      await page.getByRole("button", { name: "I’m not sure" }).first().click();
      await page
        .getByRole("button", { name: /Next picture|See how you did/ })
        .click();
      await expect(
        page
          .getByRole("button", { name: "I’m not sure" })
          .first()
          .or(page.getByRole("heading", { name: "Practice complete" })),
      ).toBeVisible();
    }
    await expect(
      page.getByRole("heading", { name: "Practice complete" }),
    ).toBeVisible();
    await user.click("Just right");
    await expect(
      page.getByRole("button", { name: "Just right" }),
    ).toHaveAttribute("aria-pressed", "true");
    user.done(1);
    await a11y(page);
    await bigTargets(page);
  });
}
