/**
 * Plan 010: the keyboard hint shows only from 1024px, so on the phone it is
 * in the DOM but hidden. Runs on the iPhone project.
 */
import { expect, test } from "@playwright/test";

test("the keyboard hint is hidden on a phone", async ({ page }) => {
  await page.goto("/lesson/0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("group", { name: "Word bank" })).toBeVisible();
  const hint = page.getByText("1 to 9 picks a word, Backspace removes, Enter checks");
  await expect(hint).toHaveCount(1);
  await expect(hint).toBeHidden();
});
