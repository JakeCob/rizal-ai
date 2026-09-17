/**
 * Phone-width screenshots of the main screens, written to
 * playwright-report/screens/ for design review. Not an assertion suite; the
 * play-through in lesson.spec.ts is the behavioral check.
 */
import { test, type Page } from "@playwright/test";

const OUT = "playwright-report/screens";

async function tap(page: Page, tokens: string[]) {
  const bank = page.getByRole("group", { name: "Word bank" });
  for (const t of tokens) await bank.getByRole("button", { name: t, exact: true }).click();
}

test("capture tree, vignette, exercise, feedback, complete", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Placeholder: the dinner.*active/ }).click();
  await page.getByRole("dialog").waitFor();
  await page.screenshot({ path: `${OUT}/01-tree.png` });

  await page.getByRole("link", { name: "Start" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.screenshot({ path: `${OUT}/02-vignette.png` });

  await page.getByRole("button", { name: "Continue" }).click();
  await tap(page, ["Marami", "ang"]);
  await page.screenshot({ path: `${OUT}/03-exercise.png` });

  await tap(page, ["bisita", "ngayong", "gabi"]);
  await page.getByRole("button", { name: "Check" }).click();
  await page.getByRole("status").waitFor();
  await page.screenshot({ path: `${OUT}/04-feedback.png` });

  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await tap(page, ["A", "young", "man", "arrived"]);
  await page.getByRole("button", { name: "Check" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.screenshot({ path: `${OUT}/05-listen-tap.png` });

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
  await page.screenshot({ path: `${OUT}/06-complete-card.png`, fullPage: true });
});
