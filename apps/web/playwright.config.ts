import { defineConfig, devices } from "@playwright/test";

// The first deliverable is defined as a play-through on a phone browser, so
// every spec runs on a phone viewport. A desktop project runs only
// desktop.spec.ts, which checks the frame around the phone column (plan 009);
// the phone specs, with the 200ms and scroll checks, never run on it. The dev
// server runs with the mock API so the tests need no database or credentials.
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://localhost:3000",
    trace: "retain-on-failure",
  },
  // iPhone 13 viewport, touch, and user agent, but on Chromium so CI only
  // needs one browser download.
  projects: [
    {
      name: "iphone",
      testIgnore: /desktop\.spec\.ts/,
      use: { ...devices["iPhone 13"], browserName: "chromium" },
    },
    {
      name: "desktop",
      testMatch: /desktop\.spec\.ts/,
      use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 800 } },
    },
  ],
  webServer: {
    command: "pnpm dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    env: { NEXT_PUBLIC_API_MODE: "mock" },
    timeout: 120_000,
  },
});
