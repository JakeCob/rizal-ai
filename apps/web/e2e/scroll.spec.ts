/**
 * Tech debt 25: on a short phone screen the newly revealed beat must not sit
 * under the fixed footer. After each vignette Continue, the current beat's
 * bottom edge is at or above the footer's top edge. A separate spec with its
 * own short viewport, so lesson.spec.ts and its 200ms check keep theirs.
 * The post-exercise beat (b3) is checked too: it is the case a scroll-to-top
 * on the way back from an exercise would break.
 * Runs against the mock API (playwright.config.ts).
 */
import { expect, test } from "@playwright/test";

// 330px tall: short enough that the beat revealed after an exercise (b3)
// starts under the footer, so the return path needs a real scroll.
// SCROLL_E2E_BASE_URL points the spec at a production server (next build and
// next start), where React runs effects once; pnpm dev's StrictMode runs them
// twice and can mask an ordering bug between Runner and VignettePlayer.
const productionUrl = process.env.SCROLL_E2E_BASE_URL;
test.use({ viewport: { width: 375, height: 330 }, ...(productionUrl ? { baseURL: productionUrl } : {}) });

test("keeps the current beat above the footer as the vignette advances", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await page.getByRole("button", { name: /Placeholder: the dinner.*active/ }).click();
  await page.getByRole("link", { name: "Start" }).click();
  await expect(page.getByText("May hapunan sa bahay ni Kapitan Tiago.")).toBeVisible();

  const story = page.getByRole("list", { name: "Story" });
  const current = story.locator('li[aria-current="step"]');
  const footer = page.locator("footer");
  const cont = () => page.getByRole("button", { name: "Continue" }).click();

  const currentClearsFooter = async () => {
    const beat = await current.boundingBox();
    const bar = await footer.boundingBox();
    if (!beat || !bar) return false;
    return beat.y + beat.height <= bar.y + 0.5;
  };

  await cont(); // b2
  await expect.poll(currentClearsFooter).toBe(true);
  await cont(); // ex1
  const bank = page.getByRole("group", { name: "Word bank" });
  for (const t of ["Marami", "ang", "bisita", "ngayong", "gabi"]) {
    await bank.getByRole("button", { name: t, exact: true }).click();
  }
  await page.getByRole("button", { name: "Check" }).click();
  await cont(); // back to the vignette, b3
  await expect.poll(currentClearsFooter).toBe(true);
  await cont(); // b4
  await expect.poll(currentClearsFooter).toBe(true);
});
