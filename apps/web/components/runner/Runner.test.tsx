/**
 * Behaviors for the runner shell:
 * - the first vignette line is shown, Continue reveals the next and dims the
 *   previous
 * - each exercise type renders from its payload with a Check button
 * - a correct check shows a green feedback sheet, a wrong one shows red with
 *   the correct answer
 * - the completion screen shows the xp total
 * - no network request happens between exercises
 */
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Runner } from "./Runner";
import { MOCK_LESSON } from "@/lib/api/fixtures";

const fetchSpy = vi.fn();

beforeEach(() => {
  vi.stubGlobal("fetch", fetchSpy);
});
afterEach(() => {
  vi.unstubAllGlobals();
  fetchSpy.mockReset();
});

async function tapTokens(user: ReturnType<typeof userEvent.setup>, tokens: string[]) {
  const bank = screen.getByRole("group", { name: /word bank/i });
  for (const t of tokens) {
    await user.click(within(bank).getByRole("button", { name: t }));
  }
}

describe("Runner", () => {
  it("plays the vignette line by line", async () => {
    const user = userEvent.setup();
    render(<Runner lesson={MOCK_LESSON} hearts={5} />);
    expect(screen.getByText("May hapunan sa bahay ni Kapitan Tiago.")).toBeInTheDocument();
    expect(screen.queryByText("Marami ang bisita ngayong gabi.")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /continue/i }));
    expect(screen.getByText("Marami ang bisita ngayong gabi.")).toBeInTheDocument();
    expect(screen.getByText("May hapunan sa bahay ni Kapitan Tiago.").closest("[data-dimmed]")).toHaveAttribute(
      "data-dimmed",
      "true",
    );
  });

  it("runs the attached exercise and grades a correct answer green", async () => {
    const user = userEvent.setup();
    render(<Runner lesson={MOCK_LESSON} hearts={5} />);
    await user.click(screen.getByRole("button", { name: /continue/i }));
    await user.click(screen.getByRole("button", { name: /continue/i }));
    expect(screen.getByText("There are many guests tonight.")).toBeInTheDocument();
    await tapTokens(user, ["Marami", "ang", "bisita", "ngayong", "gabi"]);
    await user.click(screen.getByRole("button", { name: /^check$/i }));
    const sheet = await screen.findByRole("status");
    expect(sheet).toHaveAttribute("data-result", "correct");
    expect(sheet).toHaveTextContent(/\+10 XP/);
  });

  it("shows the correct answer and spends a heart on a wrong answer", async () => {
    const user = userEvent.setup();
    render(<Runner lesson={MOCK_LESSON} hearts={5} />);
    await user.click(screen.getByRole("button", { name: /continue/i }));
    await user.click(screen.getByRole("button", { name: /continue/i }));
    await tapTokens(user, ["gabi"]);
    await user.click(screen.getByRole("button", { name: /^check$/i }));
    const sheet = await screen.findByRole("status");
    expect(sheet).toHaveAttribute("data-result", "wrong");
    expect(sheet).toHaveTextContent("Marami ang bisita ngayong gabi");
    expect(screen.getByLabelText(/hearts/i)).toHaveTextContent("4");
  });

  it("plays through every exercise type to the completion screen without fetching", async () => {
    const user = userEvent.setup();
    render(<Runner lesson={MOCK_LESSON} hearts={5} />);
    const cont = () => user.click(screen.getByRole("button", { name: /continue/i }));
    const check = () => user.click(screen.getByRole("button", { name: /^check$/i }));

    await cont();
    await cont(); // ex1 sentence_assembly
    await tapTokens(user, ["Marami", "ang", "bisita", "ngayong", "gabi"]);
    await check();
    await cont(); // feedback -> b3
    await cont(); // b3 -> b4
    await cont(); // b4 -> ex2 translate_line
    expect(screen.getByText("Dumating ang isang binata.")).toBeInTheDocument();
    await tapTokens(user, ["A", "young", "man", "arrived"]);
    await check();
    await cont(); // ex3 listen_tap
    expect(screen.getByRole("button", { name: /play audio/i })).toBeInTheDocument();
    await tapTokens(user, ["Siya", "si", "Crisostomo", "Ibarra"]);
    await check();
    await cont(); // ex4 comprehension_mc
    await user.click(screen.getByRole("radio", { name: /At Capitan Tiago's house/ }));
    await check();
    await cont(); // ex5
    await tapTokens(user, ["Dumating", "ang", "isang", "binata"]);
    await check();
    await cont(); // ex6
    await user.click(screen.getByRole("radio", { name: /Kapitan Tiago/ }));
    await check();
    await cont();

    expect(screen.getByRole("heading", { name: /lesson complete/i })).toBeInTheDocument();
    expect(screen.getByText(/60 XP/)).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
