/**
 * Plan 010 keyboard shortcuts at 1280x800: Enter advances the story, digits
 * 1 to 9 pick bank tiles by position, Backspace removes the last tile, Enter
 * checks and continues; on multiple choice a digit chooses the option; with
 * the gloss sheet open Enter does nothing; the hint is visible and is not a
 * live region. Runs on the "desktop" project only (the hint shows from lg).
 */
import { expect, test } from "@playwright/test";

test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "desktop viewport only");
});

const HINT = "1 to 9 picks a word, Backspace removes, Enter checks";

test("a lesson's first exercises played from the keyboard", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/lesson/0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d");
  const story = page.getByRole("list", { name: "Story" });
  await expect(story.getByRole("listitem")).toHaveCount(1);

  // The gloss sheet open: Enter does not advance the story.
  await page.getByRole("button", { name: "hapunan", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("dinner");
  await page.keyboard.press("Enter");
  await expect(story.getByRole("listitem")).toHaveCount(1);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toBeHidden();

  // Enter twice: the second beat, then the first exercise.
  await page.locator("body").click({ position: { x: 5, y: 5 } }); // focus back on the page, not the word
  await page.keyboard.press("Enter");
  await expect(story.getByRole("listitem")).toHaveCount(2);
  await page.keyboard.press("Enter");
  const answer = page.getByRole("group", { name: "Your answer" });
  await expect(page.getByRole("group", { name: "Word bank" })).toBeVisible();

  // The hint is visible and is not a live region.
  const hint = page.getByText(HINT);
  await expect(hint).toBeVisible();
  expect(await hint.evaluate((el) => el.closest("[aria-live], [role=status], [role=alert]"))).toBeNull();

  // 1 to 5 builds the sentence, Backspace removes gabi, 5 puts it back.
  for (const k of ["1", "2", "3", "4", "5"]) await page.keyboard.press(k);
  await expect(answer.getByRole("button")).toHaveText(["Marami", "ang", "bisita", "ngayong", "gabi"]);
  await page.keyboard.press("Backspace");
  await expect(answer.getByRole("button")).toHaveText(["Marami", "ang", "bisita", "ngayong"]);
  await page.keyboard.press("5");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("status")).toHaveAttribute("data-result", "correct");

  // Enter continues back to the story.
  await page.keyboard.press("Enter");
  await expect(page.getByRole("status")).toBeHidden();
  await expect(story.getByRole("listitem")).toHaveCount(3);

  // On to multiple choice (ex4), then "1" and Enter.
  await page.keyboard.press("Enter");
  await page.keyboard.press("Enter"); // ex2: A young man arrived
  for (const k of ["1", "2", "3", "4"]) await page.keyboard.press(k);
  await expect(answer.getByRole("button")).toHaveText(["A", "young", "man", "arrived"]);
  await page.keyboard.press("Enter");
  await expect(page.getByRole("status")).toHaveAttribute("data-result", "correct");
  await page.keyboard.press("Enter"); // ex3: Siya si Crisostomo Ibarra
  const bank = page.getByRole("group", { name: "Word bank" });
  await expect(bank.getByRole("button", { name: "Crisostomo", exact: true })).toBeVisible();
  const words = await bank.getByRole("button").allTextContents();
  for (const w of ["Siya", "si", "Crisostomo", "Ibarra"]) await page.keyboard.press(String(words.indexOf(w) + 1));
  await page.keyboard.press("Enter");
  await expect(page.getByRole("status")).toHaveAttribute("data-result", "correct");
  await page.keyboard.press("Enter"); // ex4: multiple choice
  const first = page.getByRole("radio", { name: "At Capitan Tiago's house" });
  await expect(first).toBeVisible();
  await page.keyboard.press("1");
  await expect(first).toHaveAttribute("aria-checked", "true");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("status")).toHaveAttribute("data-result", "correct");

  // ex5 by digits, then ex6: click one option, Tab to the next, Enter chooses
  // the focused option (no check yet), and a second Enter checks it.
  await page.keyboard.press("Enter");
  await expect(bank.getByRole("button", { name: "binata", exact: true })).toBeVisible();
  const words5 = await bank.getByRole("button").allTextContents();
  for (const w of ["Dumating", "ang", "isang", "binata"]) await page.keyboard.press(String(words5.indexOf(w) + 1));
  await page.keyboard.press("Enter");
  await expect(page.getByRole("status")).toHaveAttribute("data-result", "correct");
  await page.keyboard.press("Enter");
  const optionA = page.getByRole("radio", { name: "Tiya Isabel" });
  const optionB = page.getByRole("radio", { name: "Kapitan Tiago", exact: true });
  await optionA.click();
  await expect(optionA).toHaveAttribute("aria-checked", "true");
  await page.keyboard.press("Tab");
  await expect(optionB).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(optionB).toHaveAttribute("aria-checked", "true");
  await expect(optionA).toHaveAttribute("aria-checked", "false");
  await expect(page.getByRole("status")).toHaveCount(0);
  await page.keyboard.press("Enter");
  await expect(page.getByRole("status")).toHaveAttribute("data-result", "correct");
});
