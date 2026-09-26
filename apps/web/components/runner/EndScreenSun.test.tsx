/**
 * Behavior (plan 012): the completion screen shows a large faint sun centered
 * behind the score, accent gold in light and the warm dark gold in dark; the
 * out-of-hearts screen does not; the text over it stays at 4.5:1.
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { ApiClient } from "@/lib/api/client";
import { MOCK_LESSON, MOCK_TREE, MOCK_USER } from "@/lib/api/fixtures";
import { MOCK_REFLECTION, mockComplete } from "@/lib/api/fixtures.reflection";
import type { LessonOut } from "@/lib/types.generated";
import { readFileSync } from "node:fs";
import path from "node:path";
import { composite, contrast, parseTokens, resolveValue, toRgba } from "@/lib/theme/contrast";
import { Runner } from "./Runner";

/** The mock lesson cut to its first exercise: two beats, ex1, two beats, done. */
const SHORT: LessonOut = { ...MOCK_LESSON, exercises: [MOCK_LESSON.exercises[0]] };

function api(): ApiClient {
  return {
    getTree: vi.fn(async () => MOCK_TREE),
    getLesson: vi.fn(async () => SHORT),
    getMe: vi.fn(async () => MOCK_USER),
    getReflection: vi.fn(async () => MOCK_REFLECTION),
    postAttempt: vi.fn(async (body) => ({ correct: body.correct, hearts: body.correct ? 5 : 0 })),
    completeLesson: vi.fn(async (id: string) => mockComplete(id, [{ exerciseId: SHORT.exercises[0].id, correct: true }])),
    getReviewDue: vi.fn(async () => ({ items: [] })),
    postReviewAnswer: vi.fn(),
  };
}

function renderRunner(hearts: number) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <Runner lesson={SHORT} hearts={hearts} api={api()} />
    </QueryClientProvider>,
  );
}

async function playEx1(user: ReturnType<typeof userEvent.setup>, tokens: string[]) {
  const cont = () => user.click(screen.getByRole("button", { name: /continue/i }));
  await cont();
  await cont();
  const bank = screen.getByRole("group", { name: /word bank/i });
  for (const t of tokens) await user.click(within(bank).getByRole("button", { name: t }));
  await user.click(screen.getByRole("button", { name: /^check$/i }));
  await cont();
}

describe("end screen sun", () => {
  it("sits behind the score on Lesson complete", async () => {
    const user = userEvent.setup();
    const { container } = renderRunner(5);
    await playEx1(user, ["Marami", "ang", "bisita", "ngayong", "gabi"]);
    await user.click(screen.getByRole("button", { name: /continue/i }));
    await user.click(screen.getByRole("button", { name: /continue/i }));
    expect(await screen.findByRole("heading", { name: "Lesson complete" })).toBeInTheDocument();
    const sun = container.querySelector("svg[data-motif]");
    expect(sun).not.toBeNull();
    expect(sun).toHaveAttribute("aria-hidden", "true");
    expect(sun).toHaveClass("-z-10", "pointer-events-none", "text-accent", "dark:text-highlight");
    // Centered behind the score: the sun sits in the "N XP" line, inside the isolated title group.
    expect(sun?.parentElement).toHaveTextContent(/XP$/);
    expect(sun?.parentElement).toHaveClass("relative");
    expect(sun?.parentElement?.parentElement).toHaveClass("isolate");
  });

  it("is absent on Out of hearts", async () => {
    const user = userEvent.setup();
    const { container } = renderRunner(1);
    await playEx1(user, ["gabi"]);
    expect(await screen.findByRole("heading", { name: "Out of hearts" })).toBeInTheDocument();
    expect(container.querySelector("svg[data-motif]")).toBeNull();
  });

  it.each([
    ["light", "accent", 0.25],
    ["dark", "highlight", 0.8],
  ] as const)("keeps the text over it readable in %s (%s at %s)", (scheme, token, alpha) => {
    const t = parseTokens(readFileSync(path.resolve(__dirname, "../../app/globals.css"), "utf8"));
    const c = (n: string) => toRgba(resolveValue(t[scheme].get(n) as string, t[scheme]));
    const under = composite(c(token), alpha, c("background"));
    // "N XP" is large text (3:1), the correct count and streak are body text (4.5:1).
    expect(contrast(c("gold"), under)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(c("muted-foreground"), under)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(c("foreground"), under)).toBeGreaterThanOrEqual(4.5);
  });
});
