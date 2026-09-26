/**
 * Plan 011: from 1280px (xl) the card frame goes away. At 1920x1080 the tree
 * fills the app background with fixed-width sticky nav and progress columns
 * and a fluid path column, all inside a 1600px cap; a lesson keeps its 720px
 * reading column, centered, with the footer bar, the feedback and the gloss
 * sheet inside it. Runs on the "wide" project only.
 */
import { expect, test, type Locator, type Page } from "@playwright/test";

test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== "wide", "wide viewport only");
});

const OUT = "playwright-report/screens-wide";

async function boxOf(locator: Locator) {
  const b = await locator.boundingBox();
  if (!b) throw new Error("not visible");
  return b;
}

async function expectNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(0);
}

async function expectInside(outer: Locator, inner: Locator) {
  const o = await boxOf(outer);
  const i = await boxOf(inner);
  expect(i.x).toBeGreaterThanOrEqual(o.x - 0.5);
  expect(i.x + i.width).toBeLessThanOrEqual(o.x + o.width + 0.5);
}

test("the tree is full-bleed: no frame, sticky side columns, a fluid path column", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("button", { name: /Placeholder: the dinner.*active/ })).toBeVisible();

  const frame = await page.locator("[data-app-column]").evaluate((el) => {
    const s = getComputedStyle(el);
    return {
      border: s.borderTopWidth,
      shadow: s.boxShadow,
      radius: s.borderTopLeftRadius,
      background: s.backgroundColor,
      body: getComputedStyle(document.body).backgroundColor,
    };
  });
  expect(frame.border).toBe("0px");
  expect(frame.shadow).toBe("none");
  expect(frame.radius).toBe("0px");
  expect(frame.body).toBe(frame.background);

  const nav = page.getByRole("navigation", { name: "Units" });
  const main = page.getByRole("main");
  const aside = page.getByRole("complementary", { name: "Your progress" });
  await expect(nav).toBeVisible();
  await expect(aside).toBeVisible();
  const sticky = await page.evaluate(() => {
    const pos = (el: Element | null) => (el ? getComputedStyle(el).position : "missing");
    const nav = document.querySelector('nav[aria-label="Units"]');
    return { nav: pos(nav?.parentElement ?? null), aside: pos(document.querySelector('aside[aria-label="Your progress"]')) };
  });
  expect(sticky).toEqual({ nav: "sticky", aside: "sticky" });

  const n = await boxOf(nav);
  const m = await boxOf(main);
  const a = await boxOf(aside);
  expect(n.x + n.width).toBeLessThanOrEqual(m.x);
  expect(m.x + m.width).toBeLessThanOrEqual(a.x);
  expect(m.width).toBeGreaterThan(600);
  // The whole layout, from the nav's left edge to the aside's right edge, stays within 1600px and centered.
  expect(a.x + a.width - n.x).toBeLessThanOrEqual(1600);
  const viewport = page.viewportSize();
  if (!viewport) throw new Error("no viewport");
  expect(Math.abs(n.x - (viewport.width - (a.x + a.width)))).toBeLessThanOrEqual(2);

  // The path's content (the unit banner and the node list) is capped at 42rem
  // and centered inside the fluid path column.
  const banner = await boxOf(main.locator("section > header").first());
  const list = await boxOf(main.locator("section > ol").first());
  expect(banner.width).toBeLessThanOrEqual(672);
  expect(Math.abs(banner.x - m.x - (m.x + m.width - (banner.x + banner.width)))).toBeLessThanOrEqual(2);
  expect(Math.abs(list.x + list.width / 2 - (m.x + m.width / 2))).toBeLessThanOrEqual(2);

  // The header row has a bottom rule spanning the layout, from the nav's left to the aside's right.
  const header = page.getByRole("heading", { name: "RizalAI" }).locator("xpath=..");
  expect(await header.evaluate((el) => getComputedStyle(el).borderBottomWidth)).toBe("1px");
  const h = await boxOf(header);
  expect(Math.abs(h.x - n.x)).toBeLessThanOrEqual(2);
  expect(Math.abs(h.x + h.width - (a.x + a.width))).toBeLessThanOrEqual(2);
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: `${OUT}/wide-tree-011b.png`, animations: "disabled" });
});

test("a lesson keeps its 720px reading column, centered, with the footer and sheets inside", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Placeholder: the dinner.*active/ }).click();
  await page.getByRole("link", { name: "Start" }).click();
  await expect(page.getByText("May hapunan sa bahay ni Kapitan Tiago.")).toBeVisible();

  const column = page.locator("[data-app-column]");
  const viewport = page.viewportSize();
  if (!viewport) throw new Error("no viewport");
  const c = await boxOf(column);
  expect(Math.abs(c.width - 720)).toBeLessThanOrEqual(1);
  expect(Math.abs(c.x - (viewport.width - c.width) / 2)).toBeLessThanOrEqual(2);
  const frame = await column.evaluate((el) => ({
    border: getComputedStyle(el).borderTopWidth,
    shadow: getComputedStyle(el).boxShadow,
    same: getComputedStyle(el).backgroundColor === getComputedStyle(document.body).backgroundColor,
  }));
  expect(frame).toEqual({ border: "0px", shadow: "none", same: true });

  // The footer bar tracks the column.
  const footer = page.locator("footer");
  const f = await boxOf(footer);
  expect(Math.abs(f.x - c.x)).toBeLessThanOrEqual(2);
  expect(Math.abs(f.width - c.width)).toBeLessThanOrEqual(2);
  expect(Math.abs(f.y + f.height - viewport.height)).toBeLessThanOrEqual(1);
  await expectNoHorizontalOverflow(page);

  // The gloss sheet stays inside the column.
  await page.getByRole("button", { name: "hapunan", exact: true }).click();
  const gloss = page.getByRole("dialog");
  await expect(gloss).toContainText("dinner");
  await expectInside(column, gloss);
  await page.keyboard.press("Escape");
  await expect(gloss).toBeHidden();

  // The feedback sheet stays inside the column.
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  const bank = page.getByRole("group", { name: "Word bank" });
  await expect(bank).toBeVisible();

  // On a tall screen the exercise starts high (within the upper quarter),
  // not mid-screen.
  const exercise = await boxOf(page.locator("main > div").first());
  expect(exercise.y).toBeLessThan(viewport.height / 4);

  // The Check bar reads as a page bar: a top rule and an upward shadow.
  const barStyle = (el: Element) => ({ border: getComputedStyle(el).borderTopWidth, shadow: getComputedStyle(el).boxShadow });
  const checkBar = await page.locator("footer > div").first().evaluate(barStyle);
  expect(checkBar.border).toBe("1px");
  expect(checkBar.shadow).not.toBe("none");

  for (const t of ["Marami", "ang", "bisita", "ngayong", "gabi"]) await bank.getByRole("button", { name: t, exact: true }).click();
  await page.getByRole("button", { name: "Check" }).click();
  const feedback = page.getByRole("status");
  await expect(feedback).toHaveAttribute("data-result", "correct");
  await expectInside(column, feedback);
  const sheet = await feedback.evaluate(barStyle);
  expect(sheet.border).toBe("1px");
  expect(sheet.shadow).not.toBe("none");
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: `${OUT}/wide-lesson-011b.png`, animations: "disabled" });
});
