/**
 * Behaviors for the runner's network edges (SPEC.md 6.3, 6.5):
 * - the reflection is requested when the runner mounts, before any exercise
 * - every Check posts one attempt with the exercise id and the response,
 *   without blocking the feedback sheet
 * - finishing the lesson calls complete once and shows the server's XP
 * - the completion screen shows the card with the prefetched reflection
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Runner } from "./Runner";
import type { ApiClient } from "@/lib/api/client";
import { MOCK_LESSON, MOCK_TREE, MOCK_USER } from "@/lib/api/fixtures";
import { MOCK_REFLECTION, mockComplete } from "@/lib/api/fixtures.reflection";

function fakeApi(): ApiClient {
  return {
    getTree: vi.fn(async () => MOCK_TREE),
    getLesson: vi.fn(async () => MOCK_LESSON),
    getMe: vi.fn(async () => MOCK_USER),
    getReflection: vi.fn(async () => MOCK_REFLECTION),
    postAttempt: vi.fn(async (body) => ({ correct: true, hearts: 5, ...(body.correct ? {} : { correct: false, hearts: 4 }) })),
    completeLesson: vi.fn(async (id: string) =>
      mockComplete(
        id,
        MOCK_LESSON.exercises.map((e) => ({ exerciseId: e.id, correct: true })),
      ),
    ),
    getReviewDue: vi.fn(async () => ({ items: [] })),
    postReviewAnswer: vi.fn(),
  };
}

function renderRunner(api: ApiClient) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <Runner lesson={MOCK_LESSON} hearts={5} api={api} />
    </QueryClientProvider>,
  );
}

async function tapTokens(user: ReturnType<typeof userEvent.setup>, tokens: string[]) {
  const bank = screen.getByRole("group", { name: /word bank/i });
  for (const t of tokens) await user.click(within(bank).getByRole("button", { name: t }));
}

describe("Runner network edges", () => {
  it("prefetches the reflection on mount", async () => {
    const api = fakeApi();
    renderRunner(api);
    await waitFor(() => expect(api.getReflection).toHaveBeenCalledWith(MOCK_LESSON.id));
  });

  it("posts one attempt per check with the response and keeps feedback local", async () => {
    const user = userEvent.setup();
    const api = fakeApi();
    renderRunner(api);
    await user.click(screen.getByRole("button", { name: /continue/i }));
    await user.click(screen.getByRole("button", { name: /continue/i }));
    await tapTokens(user, ["Marami", "ang", "bisita", "ngayong", "gabi"]);
    await user.click(screen.getByRole("button", { name: /^check$/i }));
    expect(await screen.findByRole("status")).toHaveAttribute("data-result", "correct");
    expect(api.postAttempt).toHaveBeenCalledTimes(1);
    const body = (api.postAttempt as ReturnType<typeof vi.fn>).mock.calls[0][0];
    expect(body.exercise_id).toBe(MOCK_LESSON.exercises[0].id);
    expect(body.response).toEqual({ tokens: ["Marami", "ang", "bisita", "ngayong", "gabi"] });
    expect(body.correct).toBe(true);
    expect(typeof body.duration_ms).toBe("number");
  });

  it("completes once and shows server XP and the card", async () => {
    const user = userEvent.setup();
    const api = fakeApi();
    renderRunner(api);
    const cont = () => user.click(screen.getByRole("button", { name: /continue/i }));
    const check = () => user.click(screen.getByRole("button", { name: /^check$/i }));
    await cont();
    await cont();
    await tapTokens(user, ["Marami", "ang", "bisita", "ngayong", "gabi"]);
    await check();
    await cont();
    await cont();
    await cont();
    await tapTokens(user, ["A", "young", "man", "arrived"]);
    await check();
    await cont();
    await tapTokens(user, ["Siya", "si", "Crisostomo", "Ibarra"]);
    await check();
    await cont();
    await user.click(screen.getByRole("radio", { name: /At Capitan Tiago's house/ }));
    await check();
    await cont();
    await tapTokens(user, ["Dumating", "ang", "isang", "binata"]);
    await check();
    await cont();
    await user.click(screen.getByRole("radio", { name: /Kapitan Tiago/ }));
    await check();
    await cont();

    expect(await screen.findByRole("heading", { name: /lesson complete/i })).toBeInTheDocument();
    await waitFor(() => expect(api.completeLesson).toHaveBeenCalledTimes(1));
    expect(await screen.findByText(/60 XP/)).toBeInTheDocument();
    expect(await screen.findByText(/streak/i)).toBeInTheDocument();
    expect(await screen.findByRole("region", { name: /in rizal's voice/i })).toBeInTheDocument();
    expect(api.postAttempt).toHaveBeenCalledTimes(6);
  });
});
