// Retakes the screenshots in docs/images used by the README.
// Needs the API and web servers running with the dev seed (see README), AI_PROVIDER=ollama and
// AI_DEMO_VIEW=true for the AI screens, and some practice history for the charts, then:
//   SEED_DEV_PASSWORD=... node scripts/readme-screenshots.mjs
// BROWSER_CHANNEL picks the installed browser (default chrome; msedge also works).
import { fileURLToPath } from "node:url";

import { chromium } from "@playwright/test";

const BASE = process.env.BASE_URL ?? "http://localhost:3000";
const OUT = new URL("../../docs/images/", import.meta.url);
const password = process.env.SEED_DEV_PASSWORD;
if (!password) throw new Error("Set SEED_DEV_PASSWORD (from the root .env).");

const browser = await chromium.launch({
  channel: process.env.BROWSER_CHANNEL ?? "chrome",
});
const contextOptions = {
  viewport: { width: 1280, height: 800 },
  deviceScaleFactor: 1.5,
};

async function signIn(email) {
  const context = await browser.newContext(contextOptions);
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
  await page.waitForTimeout(4000); // numbers finish counting up
  await page.screenshot({ path: fileURLToPath(new URL(`${name}.png`, OUT)) });
  console.log("saved", name);
}

// Sign-in page (signed out).
{
  const context = await browser.newContext(contextOptions);
  const page = await context.newPage();
  await page.goto(`${BASE}/login`);
  await shot(page, "login");
  await context.close();
}

// Patient: home, the talk board, and a question with hints.
{
  const { context, page } = await signIn("patient@recovery.local");
  await shot(page, "patient-home");
  await page.goto(`${BASE}/patient/talk`);
  await shot(page, "patient-talk");
  await page.goto(`${BASE}/patient`);
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
  // Leave no session in progress for the clinician's figures.
  await context.request.post(`${BASE}/api/v1/practice/sessions/current/end`, {
    headers: { Origin: BASE },
  });
  await context.close();
}

// Clinician: the patient overview and the AI pipeline map.
{
  const { context, page } = await signIn("clinician@recovery.local");
  await page.getByRole("link", { name: "Alex" }).first().click();
  await page.waitForURL(/\/clinician\/patients\/[^/]+$/);
  const patient = page.url();
  await shot(page, "clinician-overview");
  await page.goto(`${patient}/ai-pipeline`);
  await page.setViewportSize({ width: 1280, height: 1400 }); // room for the map itself
  await shot(page, "clinician-ai-pipeline");
  await context.close();
}

await browser.close();
