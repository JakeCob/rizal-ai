import { defineConfig, devices } from "@playwright/test";

// The first deliverable is defined as a play-through on a phone browser, so
// the only project is a phone viewport. The dev server runs with the mock
// API so the test needs no database or credentials.
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
  projects: [{ name: "iphone", use: { ...devices["iPhone 13"], browserName: "chromium" } }],
  webServer: {
    command: "pnpm dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    env: { NEXT_PUBLIC_API_MODE: "mock" },
    timeout: 120_000,
  },
});
