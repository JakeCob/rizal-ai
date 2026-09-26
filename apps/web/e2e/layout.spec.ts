/**
 * The layout gate (plan 012, D39). The re-skin changes colors on phones by
 * design, so pixel hashes can no longer prove "layout unchanged". Instead,
 * over the same six states as screens.spec on the iPhone project:
 *
 * - a box snapshot: every element in the app column, the fixed footer, any
 *   dialog and any sheet, in DOM order, with its tag, role or aria-label,
 *   rect (rounded to 0.5px) and computed typography, plus the document's
 *   scroll size. Colors are left out on purpose. The same snapshot taken
 *   with the dark color scheme must equal the light one. An svg records its
 *   own box but not its children. A motif ([data-motif]) that takes part in
 *   layout records its own box the same way, so a motif in an icon's slot is
 *   held to the icon's box; an absolutely or fixed positioned motif (a
 *   decoration behind content) is left out entirely.
 * - a skeleton screenshot: every color forced to black on white, shadows,
 *   textures and opacity removed, icons and motifs hidden, the dev badge
 *   masked. It catches what boxes miss (text wrapping inside a box, a border
 *   width) while staying blind to the palette.
 *
 * Baselines come from the layout before the re-skin. A change that moves,
 * resizes or restyles type fails here; update the baselines only for a
 * layout change that is meant.
 *
 * Reduced motion is emulated so scrolls land instantly and the app's
 * reduced-motion rule ends transitions, which keeps every rect deterministic.
 */
import { writeFileSync } from "node:fs";
import { expect, test, type Page, type TestInfo } from "@playwright/test";

// Playwright applies this stylesheet inside shadow roots too. The Next.js dev
// overlay lives in the nextjs-portal element's shadow root with a transparent
// full-viewport layer, so the rules are scoped to html and body descendants
// (which never match inside a shadow root) and the portal host is hidden.
const SKELETON = `
  nextjs-portal { display: none !important; }
  html, body, body *, body *::before, body *::after {
    color: #000 !important;
    background-color: #fff !important;
    background-image: none !important;
    border-color: #000 !important;
    outline-color: #000 !important;
    text-decoration-color: #000 !important;
    caret-color: transparent !important;
    box-shadow: none !important;
    text-shadow: none !important;
    filter: none !important;
    backdrop-filter: none !important;
    opacity: 1 !important;
  }
  body svg, body [data-motif] { visibility: hidden !important; }
`;

type Box = {
  tag: string;
  role?: string;
  label?: string;
  x: number;
  y: number;
  w: number;
  h: number;
  font: string;
};

/** Wait for fonts, every finite animation, and two frames. */
async function settle(page: Page) {
  await page.evaluate(async () => {
    await document.fonts.ready;
    const finite = document.getAnimations().filter((a) => a.effect?.getComputedTiming().iterations !== Infinity);
    await Promise.all(finite.map((a) => a.finished.catch(() => undefined)));
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  });
}

async function boxes(page: Page): Promise<string> {
  await settle(page);
  const snap = await page.evaluate(() => {
    const round = (v: number) => Math.round(v * 2) / 2;
    const roots = [...document.querySelectorAll('[data-app-column], footer, [role="dialog"], [data-slot="sheet-content"]')];
    const seen = new Set<Element>();
    const out: Box[] = [];
    const visit = (el: Element) => {
      if (seen.has(el)) return;
      seen.add(el);
      const motif = el.hasAttribute("data-motif");
      if (motif && ["absolute", "fixed"].includes(getComputedStyle(el).position)) return;
      const r = el.getBoundingClientRect();
      const s = getComputedStyle(el);
      const box: Box = {
        tag: el.tagName.toLowerCase(),
        x: round(r.x),
        y: round(r.y),
        w: round(r.width),
        h: round(r.height),
        font: [s.fontSize, s.lineHeight, s.fontFamily, s.fontWeight, s.letterSpacing].join(" | "),
      };
      const role = el.getAttribute("role");
      const label = el.getAttribute("aria-label");
      if (role) box.role = role;
      if (label) box.label = label;
      out.push(box);
      if (motif || el.tagName.toLowerCase() === "svg") return; // skip svg * and a motif's inside
      for (const child of el.children) visit(child);
    };
    for (const root of roots) visit(root);
    const doc = document.documentElement;
    return {
      scrollWidth: doc.scrollWidth,
      scrollHeight: doc.scrollHeight,
      scrollY: Math.round(window.scrollY),
      elements: out,
    };
  });
  const { elements, ...page_ } = snap;
  return `{\n "page": ${JSON.stringify(page_)},\n "elements": [\n  ${elements.map((e) => JSON.stringify(e)).join(",\n  ")}\n ]\n}\n`;
}

/** toHaveScreenshot takes styles from a file, so the skeleton is written to the test's output folder. */
function skeletonPath(testInfo: TestInfo): string {
  const file = testInfo.outputPath("skeleton.css");
  writeFileSync(file, SKELETON);
  return file;
}

/** The box snapshot in light matches its baseline, dark equals light, and the skeleton matches. */
async function gate(page: Page, testInfo: TestInfo, name: string, fullPage = false) {
  const light = await boxes(page);
  expect(light).toMatchSnapshot(`${name}.json`);

  await page.emulateMedia({ colorScheme: "dark" });
  const dark = await boxes(page);
  await page.emulateMedia({ colorScheme: "light" });
  expect(dark, `${name}: the dark-scheme layout differs from light`).toBe(light);

  await settle(page);
  await expect(page).toHaveScreenshot(`${name}.png`, {
    stylePath: skeletonPath(testInfo),
    mask: [page.locator("nextjs-portal")],
    animations: "disabled",
    fullPage,
    // Glyph anti-aliasing can flip a few pixels between runs (the hearts
    // counter did in plans 010 and 011); a real layout shift moves hundreds.
    maxDiffPixels: 40,
  });
}

async function tap(page: Page, tokens: string[]) {
  const bank = page.getByRole("group", { name: "Word bank" });
  for (const t of tokens) await bank.getByRole("button", { name: t, exact: true }).click();
}

test("the layout of the six screens states is unchanged, in light and dark", async ({ page }, testInfo) => {
  test.setTimeout(90_000);
  await page.emulateMedia({ colorScheme: "light", reducedMotion: "reduce" });

  await page.goto("/");
  await page.getByRole("button", { name: /Placeholder: the dinner.*active/ }).click();
  await page.getByRole("dialog").waitFor();
  await gate(page, testInfo, "01-tree");

  await page.getByRole("link", { name: "Start" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await gate(page, testInfo, "02-vignette");

  await page.getByRole("button", { name: "Continue" }).click();
  await tap(page, ["Marami", "ang"]);
  await gate(page, testInfo, "03-exercise");

  await tap(page, ["bisita", "ngayong", "gabi"]);
  await page.getByRole("button", { name: "Check" }).click();
  await page.getByRole("status").waitFor();
  await gate(page, testInfo, "04-feedback");

  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await tap(page, ["A", "young", "man", "arrived"]);
  await page.getByRole("button", { name: "Check" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await gate(page, testInfo, "05-listen-tap");

  await tap(page, ["Siya", "si", "Crisostomo", "Ibarra"]);
  await page.getByRole("button", { name: "Check" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("radio", { name: "At Capitan Tiago's house" }).click();
  await page.getByRole("button", { name: "Check" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await tap(page, ["Dumating", "ang", "isang", "binata"]);
  await page.getByRole("button", { name: "Check" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("radio", { name: "Kapitan Tiago", exact: true }).click();
  await page.getByRole("button", { name: "Check" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("region", { name: "In Rizal's voice" }).waitFor();
  await page.getByRole("button", { name: /Spanish/ }).click();
  await page.getByText(/day streak/).waitFor(); // the completion response has landed
  await gate(page, testInfo, "06-complete-card", true);
});
