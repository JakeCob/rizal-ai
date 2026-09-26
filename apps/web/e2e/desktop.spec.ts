/**
 * Plan 010 (D38): at 1280x800 the lesson runner, end screens and practice use
 * one centered reading column up to 720px, the vignette type grows, and
 * everything fixed to the viewport (the footer, the gloss sheet, the
 * feedback) stays inside that column. Plan 011: 1280 is the xl breakpoint, so
 * there the column has no frame (full-bleed on the app background); the
 * framed card from plan 010 is checked at 1024x768 (lg, below xl). Runs on
 * the "desktop" project only; the phone specs run on "iphone".
 *
 * The mock API keeps its state in memory, so after the first completion the
 * spec moves between pages by clicking links (client-side navigation) and
 * never reloads.
 */
import { expect, test, type Locator, type Page } from "@playwright/test";

// The tablet and desktop projects share one testMatch; these assertions are
// for the desktop viewport only.
test.beforeEach(({}, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "desktop viewport only");
});

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

/**
 * The fixed footer matches the column: same x and width (D38, within 2px),
 * ending at the column's bottom edge. Its side borders match the column's:
 * 1px in the frame's colour where there is a frame (below xl), so the card
 * edge does not break at the bottom corners, and none where there is not.
 */
async function expectFooterInFrame(page: Page) {
  const footer = page.locator("footer");
  await expectInsideColumn(page, footer);
  const column = await columnBox(page);
  const box = await footer.boundingBox();
  if (!box) throw new Error("no footer");
  const viewport = page.viewportSize();
  if (!viewport) throw new Error("no viewport");
  expect(column.y + column.height).toBeLessThanOrEqual(viewport.height);
  expect(Math.abs(box.y + box.height - (column.y + column.height))).toBeLessThanOrEqual(2); // the 1px border plus rounding
  expect(Math.abs(box.x - column.x)).toBeLessThanOrEqual(2);
  expect(Math.abs(box.width - column.width)).toBeLessThanOrEqual(2);
  const borders = await page.evaluate(() => {
    const f = getComputedStyle(document.querySelector("footer") as Element);
    const c = getComputedStyle(document.querySelector("[data-app-column]") as Element);
    return {
      left: f.borderLeftWidth,
      right: f.borderRightWidth,
      color: f.borderLeftColor,
      frameWidth: c.borderLeftWidth,
      frameColor: c.borderLeftColor,
    };
  });
  expect(borders.left).toBe(borders.frameWidth);
  expect(borders.right).toBe(borders.frameWidth);
  if (borders.frameWidth !== "0px") expect(borders.color).toBe(borders.frameColor);
}

/** From md the exercise sits in the middle of the space between the header and the footer. */
async function expectExerciseBalanced(page: Page) {
  const header = await page.locator("header").first().boundingBox();
  const body = await page.locator("main > div").first().boundingBox();
  const footer = await page.locator("footer").boundingBox();
  if (!header || !body || !footer) throw new Error("runner parts missing");
  const top = header.y + header.height;
  const space = footer.y - top;
  const center = body.y + body.height / 2 - top;
  expect(center).toBeGreaterThanOrEqual(space / 3);
  expect(center).toBeLessThanOrEqual((2 * space) / 3);
}

async function expectNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(0);
}

async function tapTokens(page: Page, tokens: string[]) {
  const bank = page.getByRole("group", { name: "Word bank" });
  for (const t of tokens) await bank.getByRole("button", { name: t, exact: true }).click();
}

const cont = (page: Page) => page.getByRole("button", { name: "Continue" }).click();
const check = (page: Page) => page.getByRole("button", { name: "Check" }).click();

async function frameStyle(page: Page) {
  return page.locator("[data-app-column]").evaluate((el) => {
    const s = getComputedStyle(el);
    return {
      border: s.borderTopWidth,
      shadow: s.boxShadow,
      column: s.backgroundColor,
      page: getComputedStyle(document.body).backgroundColor,
    };
  });
}

test("at 1280 (xl) there is no frame: the tree sits on the app background", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "RizalAI" })).toBeVisible();
  const style = await frameStyle(page);
  expect(style.border).toBe("0px");
  expect(style.shadow).toBe("none");
  expect(style.page).toBe(style.column);
  await expectNoHorizontalOverflow(page);
});

test("at 1024x768 (lg, below xl) the framed card from plan 010 is unchanged", async ({ page }) => {
  await page.setViewportSize({ width: 1024, height: 768 });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "RizalAI" })).toBeVisible();
  const tree = await frameStyle(page);
  expect(tree.border).toBe("1px");
  expect(tree.shadow).not.toBe("none");
  expect(tree.page).not.toBe(tree.column);
  const column = await columnBox(page);
  expect(column.width).toBe(1024 - 48); // lg:max-w-6xl is wider than the viewport less the 24px gutters
  await expectNoHorizontalOverflow(page);

  // A lesson keeps the 720px framed column with the footer's borders on the frame's edge.
  await page.getByRole("button", { name: /Placeholder: the dinner.*active/ }).click();
  await page.getByRole("link", { name: "Start" }).click();
  await expect(page.getByText("May hapunan sa bahay ni Kapitan Tiago.")).toBeVisible();
  const lesson = await frameStyle(page);
  expect(lesson.border).toBe("1px");
  expect(lesson.shadow).not.toBe("none");
  expect((await columnBox(page)).width).toBe(720);
  const footerBorder = await page.locator("footer").evaluate((el) => getComputedStyle(el).borderLeftWidth);
  expect(footerBorder).toBe("1px");
  await expectFooterInFrame(page);
  await expectNoHorizontalOverflow(page);
});

test("a lesson, its end screens and practice fit the 720px reading column", async ({ page }) => {
  test.setTimeout(90_000);
  await page.goto("/");
  await page.getByRole("button", { name: /Placeholder: the dinner.*active/ }).click();
  await page.getByRole("link", { name: "Start" }).click();
  const firstLine = page.getByText("May hapunan sa bahay ni Kapitan Tiago.");
  await expect(firstLine).toBeVisible();

  // One centered reading column, at most 720px.
  const viewport = page.viewportSize();
  if (!viewport) throw new Error("no viewport");
  const column = await columnBox(page);
  expect(column.width).toBeLessThanOrEqual(720);
  expect(column.width).toBeGreaterThan(448);
  expect(await frameStyle(page)).toMatchObject({ border: "0px", shadow: "none" });
  expect(Math.abs(column.x - (viewport.width - column.width) / 2)).toBeLessThanOrEqual(2);
  await expectNoHorizontalOverflow(page);

  // Vignette type: at least 22px with a line height of at least 1.5.
  const type = await page.locator('ol[aria-label="Story"] p[lang="tl"]').first().evaluate((el) => {
    const s = getComputedStyle(el);
    return { size: parseFloat(s.fontSize), lineHeight: parseFloat(s.lineHeight) };
  });
  expect(type.size).toBeGreaterThanOrEqual(22);
  expect(type.lineHeight / type.size).toBeGreaterThanOrEqual(1.5);

  await expectFooterInFrame(page);

  // The gloss sheet stays inside the column.
  await page.getByRole("button", { name: "hapunan", exact: true }).click();
  const gloss = page.getByRole("dialog");
  await expect(gloss).toContainText("dinner");
  await expectInsideColumn(page, gloss);
  await page.keyboard.press("Escape");
  await expect(gloss).toBeHidden();
  await cont(page);
  await page.screenshot({ path: `${OUT}/desktop-vignette-011.png`, animations: "disabled" });

  // The first exercise and its feedback.
  await cont(page);
  await expectExerciseBalanced(page);
  await tapTokens(page, ["Marami", "ang", "bisita", "ngayong", "gabi"]);
  await expectNoHorizontalOverflow(page);
  await check(page);
  const feedback = page.getByRole("status");
  await expect(feedback).toHaveAttribute("data-result", "correct");
  await expectInsideColumn(page, feedback);
  await expectFooterInFrame(page);
  await page.screenshot({ path: `${OUT}/desktop-lesson-011.png`, animations: "disabled" });

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

  // Completion: the passage section and the reflection side by side.
  await expect(page.getByRole("heading", { name: "Lesson complete" })).toBeVisible();
  await page.getByText(/day streak/).waitFor();
  const passage = await page.getByRole("region", { name: "The passage" }).boundingBox();
  const reflection = await page.getByRole("region", { name: "In Rizal's voice" }).boundingBox();
  if (!passage || !reflection) throw new Error("completion card missing");
  expect(reflection.x).toBeGreaterThanOrEqual(passage.x + passage.width - 0.5);
  expect(Math.abs(reflection.y - passage.y)).toBeLessThanOrEqual(2);
  await expectInsideColumn(page, page.getByRole("region", { name: "The passage" }));
  await expectInsideColumn(page, page.getByRole("region", { name: "In Rizal's voice" }));
  await expectNoHorizontalOverflow(page);
  await page.screenshot({ path: `${OUT}/desktop-complete-011.png`, animations: "disabled" });

  // Replay it wrong five times to reach the out-of-hearts screen.
  await page.getByRole("link", { name: "Back to the path" }).click();
  await page.getByRole("button", { name: /Placeholder: the dinner.*done/ }).click();
  await page.getByRole("link", { name: "Review" }).click();
  await expect(firstLine).toBeVisible();
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
  const refill = page.getByRole("link", { name: "Practice to refill" });
  await expectInsideColumn(page, refill);
  await expectNoHorizontalOverflow(page);

  // Practice with due items mirrors the runner, its footer clipped to the frame.
  await refill.click();
  await expect(page.getByText(/Review 1 of \d+/)).toBeVisible();
  await expectFooterInFrame(page);
  await expectNoHorizontalOverflow(page);
  const practice = await columnBox(page);
  expect(practice.width).toBeLessThanOrEqual(720);
  await page.screenshot({ path: `${OUT}/desktop-practice-011.png`, animations: "disabled" });
});
