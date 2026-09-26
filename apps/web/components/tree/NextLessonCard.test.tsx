/**
 * Behaviors:
 * - the card names the next lesson with its unit, minutes and XP, and links
 *   to it with a link named "Go to lesson" (never "Start", which the phone
 *   popover owns)
 * - with no next lesson it shows an all-done state and no link
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { LESSON_ID, MOCK_TREE } from "@/lib/api/fixtures";
import { NextLessonCard } from "./NextLessonCard";

describe("NextLessonCard", () => {
  it("names the next lesson and links to it", () => {
    const unit = MOCK_TREE.units[0];
    render(<NextLessonCard next={{ unit, lesson: unit.lessons[0] }} />);
    expect(screen.getByText("Placeholder: the dinner at Capitan Tiago's")).toBeInTheDocument();
    expect(screen.getByText(/4 min/)).toBeInTheDocument();
    expect(screen.getByText(/60 XP/)).toBeInTheDocument();
    expect(screen.getByText(unit.title)).toBeInTheDocument();
    const link = screen.getByRole("link", { name: "Go to lesson" });
    expect(link).toHaveAttribute("href", `/lesson/${LESSON_ID}`);
    expect(screen.queryByRole("link", { name: /start/i })).toBeNull();
  });

  it("shows an all-done state when there is no next lesson", () => {
    render(<NextLessonCard next={null} />);
    expect(screen.getByText("All caught up")).toBeInTheDocument();
    expect(screen.queryByRole("link")).toBeNull();
  });
});
