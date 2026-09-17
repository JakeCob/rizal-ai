/**
 * Behaviors:
 * - unit headers and lesson nodes render from the tree
 * - the active node is a focusable button labeled with the lesson title
 * - locked nodes are labeled locked and disabled
 * - tapping the active node opens a popover with title, minutes, xp, and a
 *   Start link to the lesson route
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { SkillTree } from "./SkillTree";
import { LESSON_ID, MOCK_TREE } from "@/lib/api/fixtures";

describe("SkillTree", () => {
  it("renders the unit header and one node per lesson", () => {
    render(<SkillTree tree={MOCK_TREE} />);
    expect(screen.getByRole("heading", { name: /Noli Me Tangere: Ibarra's return/ })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /Placeholder|Chapter/ })).toHaveLength(4);
  });

  it("labels the active node and disables locked nodes", () => {
    render(<SkillTree tree={MOCK_TREE} />);
    const active = screen.getByRole("button", { name: /Placeholder: the dinner/ });
    expect(active).toBeEnabled();
    expect(active).toHaveAccessibleName(/active/i);
    const locked = screen.getByRole("button", { name: /Chapter 2/ });
    expect(locked).toBeDisabled();
    expect(locked).toHaveAccessibleName(/locked/i);
  });

  it("opens a popover with details and a Start link", async () => {
    const user = userEvent.setup();
    render(<SkillTree tree={MOCK_TREE} />);
    await user.click(screen.getByRole("button", { name: /Placeholder: the dinner/ }));
    const dialog = await screen.findByRole("dialog");
    expect(dialog).toHaveTextContent(/4 min/);
    expect(dialog).toHaveTextContent(/60 XP/);
    const start = screen.getByRole("link", { name: /start/i });
    expect(start).toHaveAttribute("href", `/lesson/${LESSON_ID}`);
  });
});
