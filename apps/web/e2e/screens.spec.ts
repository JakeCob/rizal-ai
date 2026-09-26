/**
 * Phone-width screenshots of the main screens in both color schemes, written
 * to playwright-report/screens/light/ and playwright-report/screens/dark/ for
 * design review (plan 012). Not an assertion suite; the play-through in
 * lesson.spec.ts is the behavioral check. Animations are frozen at their end
 * state so two runs give identical images, which lets a layout change be
 * checked for side effects by comparing them. The Next.js dev badge is masked
 * (and off through next.config's devIndicators), so it no longer flips pixels
 * between runs (plan 012; the layout gate itself is layout.spec.ts).
 */
import { test, type Page } from "@playwright/test";

const SCHEMES = ["light", "dark"] as const;
const badge = (page: Page) => [page.locator("nextjs-portal")];

async function tap(page: Page, tokens: string[]) {
  const bank = page.getByRole("group", { name: "Word bank" });
  for (const t of tokens) await bank.getByRole("button", { name: t, exact: true }).click();
}

for (const scheme of SCHEMES) {
  test(`capture tree, vignette, exercise, feedback, complete (${scheme})`, async ({ page }) => {
    const OUT = `playwright-report/screens/${scheme}`;
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto("/");
    await page.getByRole("button", { name: /Placeholder: the dinner.*active/ }).click();
    await page.getByRole("dialog").waitFor();
    await page.screenshot({ path: `${OUT}/01-tree.png`, animations: "disabled", mask: badge(page) });

    await page.getByRole("link", { name: "Start" }).click();
    await page.getByRole("button", { name: "Continue" }).click();
    await page.screenshot({ path: `${OUT}/02-vignette.png`, animations: "disabled", mask: badge(page) });

    await page.getByRole("button", { name: "Continue" }).click();
    await tap(page, ["Marami", "ang"]);
    await page.screenshot({ path: `${OUT}/03-exercise.png`, animations: "disabled", mask: badge(page) });

    await tap(page, ["bisita", "ngayong", "gabi"]);
    await page.getByRole("button", { name: "Check" }).click();
    await page.getByRole("status").waitFor();
    await page.screenshot({ path: `${OUT}/04-feedback.png`, animations: "disabled", mask: badge(page) });

    await page.getByRole("button", { name: "Continue" }).click();
    await page.getByRole("button", { name: "Continue" }).click();
    await page.getByRole("button", { name: "Continue" }).click();
    await tap(page, ["A", "young", "man", "arrived"]);
    await page.getByRole("button", { name: "Check" }).click();
    await page.getByRole("button", { name: "Continue" }).click();
    await page.screenshot({ path: `${OUT}/05-listen-tap.png`, animations: "disabled", mask: badge(page) });

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
    await page.screenshot({ path: `${OUT}/06-complete-card.png`, fullPage: true, animations: "disabled", mask: badge(page) });
  });
}
