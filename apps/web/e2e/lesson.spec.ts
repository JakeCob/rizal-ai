/**
 * The first deliverable, made executable: on a phone viewport, open the
 * path, start the unlocked lesson, play the vignette and every exercise, and
 * reach the completion screen with the XP total. Runs against the mock API
 * (NEXT_PUBLIC_API_MODE=mock set by playwright.config.ts).
 *
 * Also asserts the two non-functional requirements the scaffold can already
 * prove: no horizontal scroll at 375px, and exercise transitions well under
 * the 200ms budget.
 */
import { expect, test, type Page } from "@playwright/test";

async function tapTokens(page: Page, tokens: string[]) {
  const bank = page.getByRole("group", { name: "Word bank" });
  for (const t of tokens) {
    await bank.getByRole("button", { name: t, exact: true }).click();
  }
}

test("plays the placeholder lesson end to end on a phone", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "RizalAI" })).toBeVisible();

  // No horizontal scroll at phone width.
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(0);

  // Tree: active node opens a popover with Start; locked nodes are disabled.
  await expect(page.getByRole("button", { name: /Chapter 2.*locked/ })).toBeDisabled();
  await page.getByRole("button", { name: /Placeholder: the dinner.*active/ }).click();
  await expect(page.getByRole("dialog")).toContainText("60 XP");
  await page.getByRole("link", { name: "Start" }).click();

  // Vignette, line by line.
  await expect(page.getByText("May hapunan sa bahay ni Kapitan Tiago.")).toBeVisible();
  const cont = () => page.getByRole("button", { name: "Continue" }).click();
  const check = () => page.getByRole("button", { name: "Check" }).click();

  await cont();
  await cont(); // ex1
  await tapTokens(page, ["Marami", "ang", "bisita", "ngayong", "gabi"]);

  // Transition timing: from tapping Check to the feedback sheet being visible.
  const t0 = Date.now();
  await check();
  await expect(page.getByRole("status")).toHaveAttribute("data-result", "correct");
  expect(Date.now() - t0).toBeLessThan(200);

  await cont();
  await cont();
  await cont(); // ex2
  await tapTokens(page, ["A", "young", "man", "arrived"]);
  await check();
  await cont(); // ex3
  await tapTokens(page, ["Siya", "si", "Crisostomo", "Ibarra"]);
  await check();
  await cont(); // ex4
  await page.getByRole("radio", { name: "At Capitan Tiago's house" }).click();
  await check();
  await cont(); // ex5
  await tapTokens(page, ["Dumating", "ang", "isang", "binata"]);
  await check();
  await cont(); // ex6
  await page.getByRole("radio", { name: "Kapitan Tiago", exact: true }).click();
  await check();
  await cont();

  await expect(page.getByRole("heading", { name: "Lesson complete" })).toBeVisible();
  await expect(page.getByText("60 XP")).toBeVisible();
});

test("a wrong answer spends a heart and shows the correct answer", async ({ page }) => {
  await page.goto("/lesson/0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await tapTokens(page, ["gabi"]);
  await page.getByRole("button", { name: "Check" }).click();
  const sheet = page.getByRole("status");
  await expect(sheet).toHaveAttribute("data-result", "wrong");
  await expect(sheet).toContainText("Marami ang bisita ngayong gabi");
  await expect(page.getByLabel("Hearts")).toHaveText(/4/);
});
