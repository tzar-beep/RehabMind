import { defineConfig, devices } from "@playwright/test";

// E2E runs against local dev infrastructure (docker compose) with seeded dev accounts.
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:3000",
    trace: "retain-on-failure",
    permissions: ["microphone"],
    launchOptions: {
      // Fake microphone: a test tone by default, or synthetic speech from E2E_FAKE_AUDIO (wav).
      // Never real patient recordings.
      args: [
        "--use-fake-ui-for-media-stream",
        "--use-fake-device-for-media-stream",
        ...(process.env.E2E_FAKE_AUDIO
          ? [`--use-file-for-fake-audio-capture=${process.env.E2E_FAKE_AUDIO}`]
          : []),
      ],
    },
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "uv run uvicorn app.main:app --port 8000",
      cwd: "../backend",
      url: "http://localhost:8000/api/health/live",
      reuseExistingServer: true,
      timeout: 120_000,
    },
    {
      command: "uv run python -m app.workers.main",
      cwd: "../backend",
      wait: { stdout: /worker ready/ },
      reuseExistingServer: false,
      timeout: 180_000,
    },
    {
      command: "npm run dev",
      url: "http://localhost:3000/login",
      reuseExistingServer: true,
      timeout: 180_000,
    },
  ],
});
