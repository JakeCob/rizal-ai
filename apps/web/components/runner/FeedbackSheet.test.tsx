/**
 * Behavior (plan 012 review, should fix 1): the feedback sheet paints its
 * tint over an opaque page-colored base, so what shows is exactly the tint
 * over --background that the contrast test models, never the tint over
 * whatever scrolled underneath.
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { ApiClient } from "@/lib/api/client";
import { MOCK_LESSON, MOCK_TREE, MOCK_USER } from "@/lib/api/fixtures";
import { MOCK_REFLECTION } from "@/lib/api/fixtures.reflection";
import { Runner } from "./Runner";

const pending = () => new Promise<never>(() => {});
const api: ApiClient = {
  getTree: vi.fn(async () => MOCK_TREE),
  getLesson: vi.fn(async () => MOCK_LESSON),
  getMe: vi.fn(async () => MOCK_USER),
  getReflection: vi.fn(async () => MOCK_REFLECTION),
  postAttempt: vi.fn(async (body) => ({ correct: body.correct, hearts: 5 })),
  completeLesson: pending,
  getReviewDue: pending,
  postReviewAnswer: pending,
};

async function checkWith(tokens: string[]) {
  const user = userEvent.setup();
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <Runner lesson={MOCK_LESSON} hearts={5} api={api} />
    </QueryClientProvider>,
  );
  await user.click(screen.getByRole("button", { name: /continue/i }));
  await user.click(screen.getByRole("button", { name: /continue/i }));
  const bank = screen.getByRole("group", { name: /word bank/i });
  for (const t of tokens) await user.click(within(bank).getByRole("button", { name: t }));
  await user.click(screen.getByRole("button", { name: /^check$/i }));
  return screen.findByRole("status");
}

describe("feedback sheet base", () => {
  it.each([
    ["correct", ["Marami", "ang", "bisita", "ngayong", "gabi"], "success"],
    ["wrong", ["gabi"], "danger"],
  ] as const)("the %s sheet layers its tint over bg-background", async (_, tokens, tone) => {
    const sheet = await checkWith([...tokens]);
    expect(sheet).toHaveClass("bg-background", `from-${tone}/15`, `to-${tone}/15`);
    expect(sheet).not.toHaveClass(`bg-${tone}/15`);
  });
});
