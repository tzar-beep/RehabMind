// Retakes the screenshots in docs/images used by the README.
// Needs the API and web servers running with the dev seed (see README), then:
//   SEED_DEV_PASSWORD=... node scripts/readme-screenshots.mjs
import { fileURLToPath } from "node:url";

import { chromium } from "@playwright/test";

const BASE = process.env.BASE_URL ?? "http://localhost:3000";
const OUT = new URL("../../docs/images/", import.meta.url);
const password = process.env.SEED_DEV_PASSWORD;
if (!password) throw new Error("Set SEED_DEV_PASSWORD (from the root .env).");

const browser = await chromium.launch({ channel: "chrome" });

async function signIn(email) {
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
  });
  const page = await context.newPage();
  await page.goto(`${BASE}/login`);
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL(/\/(patient|clinician)$/);
  return { context, page };
}

async function shot(page, name) {
  await page.waitForLoadState("networkidle");
  // The dev-server badge is not part of the app.
  await page.addStyleTag({ content: "nextjs-portal { display: none; }" });
  await page.screenshot({ path: fileURLToPath(new URL(`${name}.png`, OUT)) });
  console.log("saved", name);
}

// Sign-in page (signed out).
{
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
  });
  const page = await context.newPage();
  await page.goto(`${BASE}/login`);
  await shot(page, "login");
  await context.close();
}

// Patient: home, a question with hints, then feedback.
{
  const { context, page } = await signIn("patient@recovery.local");
  await shot(page, "patient-home");
  await page.getByRole("link", { name: /(Start|Start new|Continue) practice/ }).click();
  await page.waitForURL(/\/patient\/practice/);
  await page.getByRole("button", { name: "I’m not sure" }).first().waitFor();
  const hint = page.getByRole("button", { name: /Show (a|another) hint/ });
  // Up to two hints, as many as the exercise offers.
  for (let i = 0; i < 2 && (await hint.isVisible()); i++) {
    await hint.click();
    await page.waitForTimeout(300);
  }
  await shot(page, "practice-hints");
  const type = page.getByRole("button", { name: "Type instead" });
  if (await type.isVisible()) await type.click();
  const box = page.getByRole("textbox").first();
  if (await box.isVisible()) {
    await box.fill("cup");
    await page.getByRole("button", { name: "Check" }).click();
  } else {
    // Word tiles or picture choices: skip, which also shows feedback.
    await page.getByRole("button", { name: "I’m not sure" }).first().click();
  }
  await page
    .getByRole("button", { name: /Next picture|See how you did/ })
    .waitFor();
  await page
    .getByText("Preparing a tip for you…")
    .waitFor({ state: "hidden", timeout: 60_000 });
  await page.waitForTimeout(1000); // let the tip finish fading in
  await shot(page, "practice-feedback");
  await context.close();
}

// Clinician: dashboard and the patient's pages.
{
  const { context, page } = await signIn("clinician@recovery.local");
  await shot(page, "clinician-home");
  await page.getByRole("link", { name: "Alex" }).first().click();
  await page.waitForURL(/\/clinician\/patients\/[^/]+$/);
  const patient = page.url();
  await shot(page, "clinician-overview");
  for (const [path, name] of [
    ["constraints", "clinician-constraints"],
    ["ai-pipeline", "clinician-ai-pipeline"],
    ["ai-generations", "clinician-ai-log"],
  ]) {
    await page.goto(`${patient}/${path}`);
    await shot(page, name);
  }
  await context.close();
}

await browser.close();
