/**
 * Behaviors for the "In Rizal's voice" card (SPEC.md 6.4):
 * - three labeled passage layers, each collapsible
 * - the reflection shows Tagalog by default and the toggle swaps to English
 *   with no network call
 * - quoted spans are visually distinct and carry their passage id
 * - a fallback payload shows only the passages
 * - the header states that the reflection is generated from cited passages
 */
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ReflectionCard } from "./ReflectionCard";
import { ES_PASSAGE_ID, MOCK_REFLECTION, MOCK_REFLECTION_FALLBACK } from "@/lib/api/fixtures.reflection";

const fetchSpy = vi.fn();
beforeEach(() => vi.stubGlobal("fetch", fetchSpy));
afterEach(() => {
  vi.unstubAllGlobals();
  fetchSpy.mockReset();
});

describe("ReflectionCard", () => {
  it("renders three labeled layers that expand to show the passage", async () => {
    const user = userEvent.setup();
    render(<ReflectionCard data={MOCK_REFLECTION} />);
    const buttons = screen.getAllByRole("button", { name: /Spanish|Tagalog|English/ });
    expect(buttons).toHaveLength(3);
    expect(buttons[1]).toHaveAccessibleName(/1909/);
    await user.click(buttons[0]);
    expect(await screen.findByText(/daba una cena\.$/)).toBeInTheDocument();
  });

  it("shows Tagalog first and toggles to English without fetching", async () => {
    const user = userEvent.setup();
    render(<ReflectionCard data={MOCK_REFLECTION} />);
    const block = screen.getByRole("region", { name: /in rizal's voice/i });
    expect(block).toHaveTextContent(/Isang hapunan lang iyon/);
    await user.click(screen.getByRole("tab", { name: /english/i }));
    expect(block).toHaveTextContent(/It was only a dinner/);
    expect(block).not.toHaveTextContent(/Isang hapunan/);
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("marks quoted spans distinctly with their passage id", () => {
    render(<ReflectionCard data={MOCK_REFLECTION} />);
    const block = screen.getByRole("region", { name: /in rizal's voice/i });
    const quotes = within(block).getAllByRole("mark");
    expect(quotes).toHaveLength(1);
    expect(quotes[0]).toHaveTextContent("daba una cena");
    expect(quotes[0]).toHaveAttribute("data-passage-id", ES_PASSAGE_ID);
  });

  it("states that the reflection is generated from cited passages", () => {
    render(<ReflectionCard data={MOCK_REFLECTION} />);
    expect(screen.getByText(/generated from the cited passages/i)).toBeInTheDocument();
  });

  it("shows only the passages for a fallback payload", () => {
    render(<ReflectionCard data={MOCK_REFLECTION_FALLBACK} />);
    expect(screen.queryByRole("region", { name: /in rizal's voice/i })).not.toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /Spanish|Tagalog|English/ })).toHaveLength(3);
  });
});
