/**
 * Plan 010 (D38): at 768x1024 the frame widens to the reading column and
 * sits inside the viewport; the fixed footer (runner and practice) matches
 * the column's x and width and ends at its bottom; the gloss sheet and the
 * feedback stay inside it; the exercise sits mid-card; and all type keeps the
 * phone scale (it grows only from 1024px, so landscape phones keep it too).
 * A second case forces a classic scrollbar, which takes layout width, and
 * checks that the fixed footer still matches the narrower frame.
 * Runs on the "tablet" project only.
 *
 * The mock API keeps its state in memory, so the spec moves between pages by
 * clicking links (client-side navigation) and never reloads.
 */
import { chromium, expect, test, type Locator, type Page } from "@playwright/test";

// The tablet and desktop projects share one testMatch; these assertions are
// for the tablet viewport only.
test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== "tablet", "tablet viewport only");
});

const OUT = "playwright-report/screens-tablet";

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

/** The fixed footer matches the column's x and width and ends at its bottom edge. */
async function expectFooterMatchesFrame(page: Page) {
  const column = await columnBox(page);
  const box = await page.locator("footer").boundingBox();
  if (!box) throw new Error("no footer");
  expect(Math.abs(box.x - column.x)).toBeLessThanOrEqual(2);
  expect(Math.abs(box.width - column.width)).toBeLessThanOrEqual(2);
  expect(Math.abs(box.y + box.height - (column.y + column.height))).toBeLessThanOrEqual(2);
}

async function expectNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(0);
}

async function fontSize(element: Locator) {
  return element.evaluate((el) => parseFloat(getComputedStyle(el).fontSize));
}

async function tapTokens(page: Page, tokens: string[]) {
  const bank = page.getByRole("group", { name: "Word bank" });
  for (const t of tokens) await bank.getByRole("button", { name: t, exact: true }).click();
}

const cont = (page: Page) => page.getByRole("button", { name: "Continue" }).click();
const check = (page: Page) => page.getByRole("button", { name: "Check" }).click();

async function startLesson(page: Page) {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "RizalAI" })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await page.getByRole("button", { name: /Placeholder: the dinner.*active/ }).click();
  await page.getByRole("link", { name: "Start" }).click();
  await expect(page.getByText("May hapunan sa bahay ni Kapitan Tiago.")).toBeVisible();
}

/** The card from plans 009 and 010: a 1px border, a shadow, and the desk around it. */
async function expectCard(page: Page) {
  const style = await page.locator("[data-app-column]").evaluate((el) => {
    const s = getComputedStyle(el);
    return { border: s.borderTopWidth, shadow: s.boxShadow, column: s.backgroundColor, body: getComputedStyle(document.body).backgroundColor };
  });
  expect(style.border).toBe("1px");
  expect(style.shadow).not.toBe("none");
  expect(style.body).not.toBe(style.column);
  // The banig texture surrounds the card (plan 012).
  expect(await page.evaluate(() => getComputedStyle(document.body).backgroundImage)).toMatch(/^url\(/);
}

test("the tree and a lesson sit in the card at 768 (below xl)", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "RizalAI" })).toBeVisible();
  await expectCard(page);
  await page.getByRole("button", { name: /Placeholder: the dinner.*active/ }).click();
  await page.getByRole("link", { name: "Start" }).click();
  await expect(page.getByText("May hapunan sa bahay ni Kapitan Tiago.")).toBeVisible();
  await expectCard(page);
});

test("a lesson, its end screens and practice at 768x1024 keep the phone type inside a wider frame", async ({ page }) => {
  test.setTimeout(90_000);
  await startLesson(page);

  // The frame is wider than the phone column and sits inside the viewport.
  const viewport = page.viewportSize();
  if (!viewport) throw new Error("no viewport");
  const column = await columnBox(page);
  expect(column.width).toBeGreaterThan(448);
  expect(column.width).toBeLessThanOrEqual(720);
  expect(column.x).toBeGreaterThanOrEqual(0);
  expect(column.x + column.width).toBeLessThanOrEqual(viewport.width);
  expect(column.y).toBeGreaterThanOrEqual(0);
  expect(column.y + column.height).toBeLessThanOrEqual(viewport.height);
  await expectNoHorizontalOverflow(page);
  await expectFooterMatchesFrame(page);

  // Phone type scale in the vignette: the line stays under 22px.
  expect(await fontSize(page.locator('ol[aria-label="Story"] p[lang="tl"]').first())).toBeLessThan(22);

  // The gloss sheet stays inside the frame.
  await page.getByRole("button", { name: "hapunan", exact: true }).click();
  const gloss = page.getByRole("dialog");
  await expect(gloss).toContainText("dinner");
  await expectInsideColumn(page, gloss);
  await page.keyboard.press("Escape");
  await expect(gloss).toBeHidden();

  // The speaker label on the second beat keeps its phone size (12px).
  await cont(page);
  expect(await fontSize(page.getByText("Tiya Isabel", { exact: true }))).toBe(12);

  // The first exercise sits mid-card, and its feedback stays inside the frame.
  await cont(page);
  const header = await page.locator("header").first().boundingBox();
  const body = await page.locator("main > div").first().boundingBox();
  const bar = await page.locator("footer").boundingBox();
  if (!header || !body || !bar) throw new Error("runner parts missing");
  const top = header.y + header.height;
  const center = body.y + body.height / 2 - top;
  expect(center).toBeGreaterThanOrEqual((bar.y - top) / 3);
  expect(center).toBeLessThanOrEqual((2 * (bar.y - top)) / 3);
  await tapTokens(page, ["Marami", "ang", "bisita", "ngayong", "gabi"]);
  await check(page);
  const feedback = page.getByRole("status");
  await expect(feedback).toHaveAttribute("data-result", "correct");
  await expectInsideColumn(page, feedback);
  await expectFooterMatchesFrame(page);
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: `${OUT}/tablet-lesson-010b.png`, animations: "disabled" });

  // The rest of the lesson, answered correctly.
  await cont(page);
  await cont(page);
  await cont(page);
  await tapTokens(page, ["A", "young", "man", "arrived"]);
  await check(page);
  await cont(page);
  await tapTokens(page, ["Siya", "si", "Crisostomo", "Ibarra"]);
  await check(page);
  await cont(page);
  await page.getByRole("radio", { name: "At Capitan Tiago's house" }).click();
  await check(page);
  await cont(page);
  await tapTokens(page, ["Dumating", "ang", "isang", "binata"]);
  await check(page);
  await cont(page);
  await page.getByRole("radio", { name: "Kapitan Tiago", exact: true }).click();
  await check(page);
  await cont(page);

  // Completion keeps the phone type: title 30px, XP 48px, passage 15px, reflection 17px.
  await expect(page.getByRole("heading", { name: "Lesson complete" })).toBeVisible();
  await page.getByText(/day streak/).waitFor();
  expect(await fontSize(page.getByRole("heading", { name: "Lesson complete" }))).toBe(30);
  expect(await fontSize(page.getByText("60 XP", { exact: true }))).toBe(48);
  await page.getByRole("button", { name: /Spanish/ }).click();
  expect(await fontSize(page.locator("[data-passage-id]").first())).toBe(15);
  expect(await fontSize(page.getByRole("region", { name: "In Rizal's voice" }).locator("p[lang]"))).toBe(17);
  await expectNoHorizontalOverflow(page);

  // Replay it wrong five times to reach the out-of-hearts screen.
  await page.getByRole("link", { name: "Back to the path" }).click();
  await page.getByRole("button", { name: /Placeholder: the dinner.*done/ }).click();
  await page.getByRole("link", { name: "Review" }).click();
  await cont(page);
  await cont(page);
  await tapTokens(page, ["gabi"]);
  await check(page);
  await cont(page);
  await cont(page);
  await cont(page);
  await tapTokens(page, ["arrived"]);
  await check(page);
  await cont(page);
  await tapTokens(page, ["Ibarra"]);
  await check(page);
  await cont(page);
  await page.getByRole("radio", { name: "At the church" }).click();
  await check(page);
  await cont(page);
  await tapTokens(page, ["binata"]);
  await check(page);
  await cont(page);
  await expect(page.getByRole("heading", { name: "Out of hearts" })).toBeVisible();
  expect(await fontSize(page.getByRole("heading", { name: "Out of hearts" }))).toBe(30);
  const refill = page.getByRole("link", { name: "Practice to refill" });
  await expectInsideColumn(page, refill);

  // Practice with due items: its footer matches the frame like the runner's.
  await refill.click();
  await expect(page.getByText(/Review 1 of \d+/)).toBeVisible();
  await expectFooterMatchesFrame(page);
  await expectNoHorizontalOverflow(page);
});

test("with a classic scrollbar the fixed footer still matches the frame", async ({ baseURL }) => {
  // Playwright starts headless Chromium with --hide-scrollbars, and a launch
  // option cannot change per test, so this case launches its own browser
  // without it. A styled scrollbar is then a classic one that takes layout
  // width, while the md query still counts the full 768px.
  const browser = await chromium.launch({ ignoreDefaultArgs: ["--hide-scrollbars"] });
  try {
    const page = await browser.newPage({ baseURL, viewport: { width: 768, height: 1024 } });
    await page.addInitScript(() => {
      document.addEventListener("DOMContentLoaded", () => {
        const style = document.createElement("style");
        style.textContent = "html { overflow-y: scroll } ::-webkit-scrollbar { width: 15px }";
        document.head.appendChild(style);
      });
    });
    await startLesson(page);
    const scrollbar = await page.evaluate(() => window.innerWidth - document.documentElement.clientWidth);
    expect(scrollbar).toBeGreaterThan(0);
    await expectFooterMatchesFrame(page);

    // The gloss sheet also stays inside the narrower frame.
    await page.getByRole("button", { name: "hapunan", exact: true }).click();
    const gloss = page.getByRole("dialog");
    await expect(gloss).toContainText("dinner");
    await expectInsideColumn(page, gloss);
  } finally {
    await browser.close();
  }
});
