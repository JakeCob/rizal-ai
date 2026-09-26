import { defineConfig, devices } from "@playwright/test";

// The first deliverable is defined as a play-through on a phone browser, so
// every phone spec runs on the iPhone project, including the 200ms check,
// scroll.spec and screens.spec. The tablet (768x1024), desktop (1280x800)
// and wide (1920x1080) projects run only the desktop, tablet and wide specs,
// which check the wider layouts (plan 010, D38; plan 011 full-bleed from
// 1280px). Each of those files skips itself on the projects it is not for.
// The dev server runs with the mock API so the tests need no database or
// credentials.
const WIDE_SPECS = /(desktop|tablet|wide).*\.spec\.ts/;

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
      testIgnore: WIDE_SPECS,
      use: { ...devices["iPhone 13"], browserName: "chromium" },
    },
    {
      name: "tablet",
      testMatch: WIDE_SPECS,
      use: { ...devices["Desktop Chrome"], viewport: { width: 768, height: 1024 } },
    },
    {
      name: "desktop",
      testMatch: WIDE_SPECS,
      use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 800 } },
    },
    {
      name: "wide",
      testMatch: WIDE_SPECS,
      use: { ...devices["Desktop Chrome"], viewport: { width: 1920, height: 1080 } },
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
