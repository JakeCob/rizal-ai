/**
 * Plan 010 (D38): the tree at tablet and desktop widths. At 1280x800 a units
 * nav, the path in a main landmark and a progress aside sit left to right;
 * at 768x1024 the nav and the path show and the header keeps the stats.
 * The mock API keeps its state in memory, so after the lesson the spec goes
 * back to the tree by clicking a link, never by reloading.
 */
import { expect, test, type Page } from "@playwright/test";

const DESKTOP_OUT = "playwright-report/screens-desktop";
const TABLET_OUT = "playwright-report/screens-tablet";

async function expectNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(0);
}

async function box(page: Page, selector: Parameters<Page["getByRole"]>) {
  const b = await page.getByRole(...selector).boundingBox();
  if (!b) throw new Error(`${selector[1]?.name} not visible`);
  return b;
}

async function playLesson(page: Page) {
  const bank = () => page.getByRole("group", { name: "Word bank" });
  const tap = async (tokens: string[]) => {
    for (const t of tokens) await bank().getByRole("button", { name: t, exact: true }).click();
  };
  const cont = () => page.getByRole("button", { name: "Continue" }).click();
  const check = () => page.getByRole("button", { name: "Check" }).click();
  await expect(page.getByText("May hapunan sa bahay ni Kapitan Tiago.")).toBeVisible();
  await cont();
  await cont();
  await tap(["Marami", "ang", "bisita", "ngayong", "gabi"]);
  await check();
  await cont();
  await cont();
  await cont();
  await tap(["A", "young", "man", "arrived"]);
  await check();
  await cont();
  await tap(["Siya", "si", "Crisostomo", "Ibarra"]);
  await check();
  await cont();
  await page.getByRole("radio", { name: "At Capitan Tiago's house" }).click();
  await check();
  await cont();
  await tap(["Dumating", "ang", "isang", "binata"]);
  await check();
  await cont();
  await page.getByRole("radio", { name: "Kapitan Tiago", exact: true }).click();
  await check();
  await cont();
  await expect(page.getByRole("heading", { name: "Lesson complete" })).toBeVisible();
  await page.getByText(/day streak/).waitFor();
}

test("desktop: units nav, path and progress aside, left to right", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "desktop viewport only");
  test.setTimeout(60_000);
  await page.goto("/");
  const nav = page.getByRole("navigation", { name: "Units" });
  const main = page.getByRole("main");
  const aside = page.getByRole("complementary", { name: "Your progress" });
  await expect(nav).toBeVisible();
  await expect(main).toBeVisible();
  await expect(aside).toBeVisible();
  await expect(page.getByRole("button", { name: /Placeholder: the dinner.*active/ })).toBeVisible();

  // Left to right without overlap.
  const n = await box(page, ["navigation", { name: "Units" }]);
  const m = await box(page, ["main"]);
  const a = await box(page, ["complementary", { name: "Your progress" }]);
  expect(n.x + n.width).toBeLessThanOrEqual(m.x);
  expect(m.x + m.width).toBeLessThanOrEqual(a.x);

  // The header stats give way to the aside at lg.
  await expect(page.getByLabel("Streak")).toBeHidden();
  await expect(page.getByLabel("Total XP")).toBeHidden();

  // The nav's text lines up with the wordmark's (text, not boxes: padding
  // would hide an offset).
  const textLeft = (el: Element) => {
    const range = document.createRange();
    range.selectNodeContents(el);
    return range.getBoundingClientRect().left;
  };
  const brand = await page.getByRole("heading", { name: "RizalAI" }).evaluate(textLeft);
  const unitsLabel = await nav.getByText("Units", { exact: true }).evaluate(textLeft);
  const unitTitle = await nav.getByText("Noli Me Tangere: Ibarra's return").evaluate(textLeft);
  expect(Math.abs(unitsLabel - brand)).toBeLessThanOrEqual(1);
  expect(Math.abs(unitTitle - brand)).toBeLessThanOrEqual(1);

  // The current unit is marked, and its progress bar has a visible track.
  await expect(nav.getByRole("link", { name: /Ibarra's return/ })).toHaveAttribute("aria-current", "true");
  const colors = await nav.evaluate((el) => ({
    track: getComputedStyle(el.querySelector('[data-slot="progress-track"]') as Element).backgroundColor,
    column: getComputedStyle(document.querySelector("[data-app-column]") as Element).backgroundColor,
  }));
  expect(colors.track).not.toBe(colors.column);

  // The path swings both ways around the path column's center.
  const offsets = await main.evaluate((el) => {
    const mid = el.getBoundingClientRect().left + el.getBoundingClientRect().width / 2;
    return [...el.querySelectorAll("ol > li button")].map((b) => {
      const r = b.getBoundingClientRect();
      return r.left + r.width / 2 - mid;
    });
  });
  const right = Math.max(...offsets);
  const left = -Math.min(...offsets);
  expect(right).toBeGreaterThan(40);
  expect(left).toBeGreaterThan(40);
  expect(Math.abs(right - left)).toBeLessThanOrEqual(2);

  // Bigger nodes.
  const node = await box(page, ["button", { name: /Placeholder: the dinner.*active/ }]);
  expect(node.width).toBeGreaterThanOrEqual(88);
  expect(node.height).toBeGreaterThanOrEqual(88);

  // The nav links to the unit, and the card links to the active lesson.
  await expect(nav.getByRole("link", { name: /Ibarra's return/ })).toHaveAttribute("href", /#unit-/);
  const go = aside.getByRole("link", { name: "Go to lesson" });
  await expect(go).toHaveAttribute("href", "/lesson/0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d");
  await expect(aside).toContainText("Placeholder: the dinner at Capitan Tiago's");
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: `${DESKTOP_OUT}/desktop-tree-010b.png`, animations: "disabled" });

  // Play the lesson from the card, then go back client-side.
  await go.click();
  await playLesson(page);
  await page.getByRole("link", { name: "Back to the path" }).click();
  await expect(aside.locator("dd").nth(1)).toHaveText("60");
  await expect(aside.locator("dd").nth(0)).toHaveText(/1 day/);
  await expect(page.getByRole("button", { name: /Placeholder: the dinner.*done/ })).toBeVisible();
  await expect(aside).toContainText("All caught up");
  await expect(nav).toContainText("1 of 4 done");
  await expectNoHorizontalOverflow(page);
});

test("tablet: units nav and path, the aside hidden, the header stats kept", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "tablet", "tablet viewport only");
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "RizalAI" })).toBeVisible();
  const nav = page.getByRole("navigation", { name: "Units" });
  await expect(nav).toBeVisible();
  await expect(page.getByRole("main")).toBeVisible();
  await expect(page.getByRole("button", { name: /Placeholder: the dinner.*active/ })).toBeVisible();
  await expect(page.locator('aside[aria-label="Your progress"]')).toHaveCount(1);
  await expect(page.getByRole("complementary", { name: "Your progress" })).toBeHidden();
  await expect(page.getByLabel("Streak")).toBeVisible();
  await expect(page.getByLabel("Total XP")).toBeVisible();
  await expect(page.getByLabel("Hearts")).toBeVisible();

  const n = await box(page, ["navigation", { name: "Units" }]);
  const m = await box(page, ["main"]);
  expect(n.x + n.width).toBeLessThanOrEqual(m.x);
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: `${TABLET_OUT}/tablet-tree-010b.png`, animations: "disabled" });
});
