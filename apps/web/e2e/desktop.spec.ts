/**
 * Plan 009: on a desktop viewport the phone column is dressed as a framed
 * card on a distinct page background, and everything the lesson shows stays
 * inside that column. Runs only on the "desktop" project (1280x800); the
 * phone specs are unaffected and run only on "iphone".
 */
import { expect, test, type Locator, type Page } from "@playwright/test";

const OUT = "playwright-report/screens-desktop";

async function columnBox(page: Page) {
  const box = await page.locator("[data-app-column]").boundingBox();
  if (!box) throw new Error("no app column");
  return box;
}

async function expectInsideColumn(page: Page, element: Locator) {
  const column = await columnBox(page);
  const box = await element.boundingBox();
  if (!box) throw new Error("element not visible");
  expect(box.x).toBeGreaterThanOrEqual(column.x - 0.5);
  expect(box.x + box.width).toBeLessThanOrEqual(column.x + column.width + 0.5);
}

test("the column is a centered, framed card on a distinct background", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "RizalAI" })).toBeVisible();

  const viewport = page.viewportSize();
  if (!viewport) throw new Error("no viewport");
  const box = await columnBox(page);
  expect(box.width).toBeLessThanOrEqual(448);
  expect(Math.abs(box.x - (viewport.width - box.width) / 2)).toBeLessThanOrEqual(2);

  const style = await page.locator("[data-app-column]").evaluate((el) => {
    const s = getComputedStyle(el);
    return {
      border: s.borderTopWidth,
      shadow: s.boxShadow,
      column: s.backgroundColor,
      page: getComputedStyle(document.body).backgroundColor,
    };
  });
  expect(style.border).not.toBe("0px");
  expect(style.shadow).not.toBe("none");
  expect(style.page).not.toBe(style.column);

  await page.screenshot({ path: `${OUT}/desktop-tree.png` });
});

test("the lesson's footer, gloss sheet and feedback stay inside the column", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Placeholder: the dinner.*active/ }).click();
  await page.getByRole("link", { name: "Start" }).click();
  await expect(page.getByText("May hapunan sa bahay ni Kapitan Tiago.")).toBeVisible();

  await expectInsideColumn(page, page.locator("footer"));
  const column = await columnBox(page);
  const footer = await page.locator("footer").boundingBox();
  if (!footer) throw new Error("no footer");
  // The frame fits the viewport and the footer ends at its bottom edge.
  expect(column.y + column.height).toBeLessThanOrEqual(800);
  expect(Math.abs(footer.y + footer.height - (column.y + column.height))).toBeLessThanOrEqual(2); // the 1px border plus rounding

  await page.getByRole("button", { name: "hapunan", exact: true }).click();
  const gloss = page.getByRole("dialog");
  await expect(gloss).toContainText("dinner");
  await expectInsideColumn(page, gloss);
  await page.screenshot({ path: `${OUT}/desktop-gloss.png`, animations: "disabled" });
  await page.keyboard.press("Escape");
  await expect(gloss).toBeHidden();

  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  const bank = page.getByRole("group", { name: "Word bank" });
  for (const t of ["Marami", "ang", "bisita", "ngayong", "gabi"]) {
    await bank.getByRole("button", { name: t, exact: true }).click();
  }
  await page.getByRole("button", { name: "Check" }).click();
  const feedback = page.getByRole("status");
  await expect(feedback).toHaveAttribute("data-result", "correct");
  await expectInsideColumn(page, feedback);
  await page.screenshot({ path: `${OUT}/desktop-lesson.png`, animations: "disabled" });
});

test("the practice page fits the frame too", async ({ page }) => {
  await page.goto("/practice");
  await page.waitForLoadState("networkidle");
  const column = await columnBox(page);
  expect(column.y + column.height).toBeLessThanOrEqual(800);
  await page.screenshot({ path: `${OUT}/desktop-practice.png`, animations: "disabled" });
});
