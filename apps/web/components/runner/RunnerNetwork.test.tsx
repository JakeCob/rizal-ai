/**
 * Behaviors for the runner's network edges (SPEC.md 6.3, 6.5):
 * - the reflection is requested when the runner mounts, before any exercise
 * - every Check posts one attempt with the exercise id and the response,
 *   without blocking the feedback sheet
 * - finishing the lesson calls complete once and shows the server's XP
 * - the completion screen shows the card with the prefetched reflection
 * - keyboard (plan 010): Enter advances the story, digits pick bank tiles by
 *   position, Backspace removes the last, Enter checks and continues; Enter
 *   on a focused option or on the focused Check button posts exactly one
 *   attempt; digits choose an option; Enter with the gloss sheet open does
 *   nothing
 * - Enter on a focused option that is not the chosen one chooses it and
 *   posts nothing; a second Enter checks it, with one attempt for the new
 *   choice (review 010-c, should fix 1)
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

  it("plays the first exercise from the keyboard", async () => {
    const user = userEvent.setup();
    const api = fakeApi();
    renderRunner(api);
    const beats = () => within(screen.getByRole("list", { name: "Story" })).getAllByRole("listitem");
    expect(beats()).toHaveLength(1);
    await user.keyboard("{Enter}");
    expect(beats()).toHaveLength(2);
    await user.keyboard("{Enter}");
    const answer = await screen.findByRole("group", { name: /your answer/i });
    await user.keyboard("12345");
    expect(within(answer).getAllByRole("button").map((b) => b.textContent)).toEqual(["Marami", "ang", "bisita", "ngayong", "gabi"]);
    await user.keyboard("{Backspace}");
    expect(within(answer).queryByRole("button", { name: "gabi" })).toBeNull();
    await user.keyboard("5");
    await user.keyboard("{Enter}");
    expect(await screen.findByRole("status")).toHaveAttribute("data-result", "correct");
    expect(api.postAttempt).toHaveBeenCalledTimes(1);
    await user.keyboard("{Enter}");
    expect(screen.queryByRole("status")).toBeNull();
    expect(screen.getByRole("list", { name: "Story" })).toBeInTheDocument();
  });

  it("does not check from the keyboard with no answer", async () => {
    const user = userEvent.setup();
    const api = fakeApi();
    renderRunner(api);
    await user.keyboard("{Enter}{Enter}");
    await screen.findByRole("group", { name: /word bank/i });
    await user.keyboard("{Enter}");
    expect(screen.queryByRole("status")).toBeNull();
    expect(api.postAttempt).not.toHaveBeenCalled();
  });

  it("posts one attempt when Enter is pressed on the focused Check button", async () => {
    const user = userEvent.setup();
    const api = fakeApi();
    renderRunner(api);
    await user.click(screen.getByRole("button", { name: /continue/i }));
    await user.click(screen.getByRole("button", { name: /continue/i }));
    await tapTokens(user, ["Marami", "ang", "bisita", "ngayong", "gabi"]);
    screen.getByRole("button", { name: /^check$/i }).focus();
    await user.keyboard("{Enter}");
    expect(await screen.findByRole("status")).toHaveAttribute("data-result", "correct");
    expect(api.postAttempt).toHaveBeenCalledTimes(1);
  });

  it("chooses an option by digit and checks once with Enter on a focused option", async () => {
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
    expect(api.postAttempt).toHaveBeenCalledTimes(3);

    await user.keyboard("2");
    expect(screen.getByRole("radio", { name: "At the church" })).toHaveAttribute("aria-checked", "true");
    await user.click(screen.getByRole("radio", { name: /At Capitan Tiago's house/ }));
    expect(screen.getByRole("radio", { name: /At Capitan Tiago's house/ })).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(await screen.findByRole("status")).toHaveAttribute("data-result", "correct");
    expect(api.postAttempt).toHaveBeenCalledTimes(4);
  });

  it("does not advance with Enter while the gloss sheet is open", async () => {
    const user = userEvent.setup();
    const api = fakeApi();
    renderRunner(api);
    await user.click(screen.getByRole("button", { name: "hapunan" }));
    await screen.findByRole("dialog");
    await user.keyboard("{Enter}");
    expect(within(screen.getByRole("list", { name: "Story" })).getAllByRole("listitem")).toHaveLength(1);
  });

  it("chooses the focused option on Enter before checking it", async () => {
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
    expect(api.postAttempt).toHaveBeenCalledTimes(3);

    const wrong = screen.getByRole("radio", { name: "At the church" });
    const right = screen.getByRole("radio", { name: /At Capitan Tiago's house/ });
    await user.click(wrong);
    right.focus();
    await user.keyboard("{Enter}");
    expect(right).toHaveAttribute("aria-checked", "true");
    expect(wrong).toHaveAttribute("aria-checked", "false");
    expect(screen.queryByRole("status")).toBeNull();
    expect(api.postAttempt).toHaveBeenCalledTimes(3);

    await user.keyboard("{Enter}");
    expect(await screen.findByRole("status")).toHaveAttribute("data-result", "correct");
    expect(api.postAttempt).toHaveBeenCalledTimes(4);
    const body = (api.postAttempt as ReturnType<typeof vi.fn>).mock.calls[3][0];
    expect(body.response).toEqual({ optionIndex: 0 });
    expect(body.correct).toBe(true);
  });
});
