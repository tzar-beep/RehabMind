// Temporary: run the suite with the locally installed Chrome (no browser download).
import base from "./playwright.config";
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  ...base,
  projects: [
    { name: "chrome", use: { ...devices["Desktop Chrome"], channel: "chrome" } },
  ],
});
