/**
 * Behaviors:
 * - the learner's streak, total XP and hearts render as a definition list
 *   (term and value pairs), with no aria-labels that would duplicate the
 *   header's Streak, Total XP and Hearts labels
 * - while the learner is loading every value shows a dash
 * - the list is a polite live region, so a screen reader hears the stats
 *   change on desktop, where the header's live stats are hidden
 */
import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MOCK_USER } from "@/lib/api/fixtures";
import { ProgressPanel } from "./ProgressPanel";

describe("ProgressPanel", () => {
  it("renders the three stats as a definition list", () => {
    const { container } = render(<ProgressPanel user={{ ...MOCK_USER, streak_count: 3, total_xp: 60, hearts: 4 }} />);
    const dl = container.querySelector("dl");
    expect(dl).not.toBeNull();
    const terms = within(dl as HTMLElement).getAllByRole("term").map((t) => t.textContent);
    expect(terms).toEqual(["Streak", "Total XP", "Hearts"]);
    const values = within(dl as HTMLElement).getAllByRole("definition").map((d) => d.textContent);
    expect(values).toEqual(["3 days", "60", "4"]);
    expect(screen.queryByLabelText("Total XP")).toBeNull();
    expect(screen.queryByLabelText("Streak")).toBeNull();
    expect(screen.queryByLabelText("Hearts")).toBeNull();
  });

  it("says 1 day for a one-day streak", () => {
    render(<ProgressPanel user={{ ...MOCK_USER, streak_count: 1 }} />);
    expect(screen.getAllByRole("definition")[0]).toHaveTextContent("1 day");
  });

  it("shows dashes while the learner is loading", () => {
    render(<ProgressPanel user={undefined} />);
    expect(screen.getAllByRole("definition").map((d) => d.textContent)).toEqual(["–", "–", "–"]);
  });

  it("is a polite live region", () => {
    const { container } = render(<ProgressPanel user={MOCK_USER} />);
    expect(container.querySelector("dl")).toHaveAttribute("aria-live", "polite");
  });
});
