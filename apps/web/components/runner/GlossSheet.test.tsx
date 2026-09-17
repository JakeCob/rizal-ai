/**
 * Behavior (SPEC.md 6.3): tapping a Tagalog word that is in target_vocab
 * opens a sheet with its English gloss; other words are plain text.
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { VignettePlayer } from "./VignettePlayer";
import { MOCK_LESSON } from "@/lib/api/fixtures";

describe("gloss sheet", () => {
  it("opens a gloss for a vocabulary word and not for other words", async () => {
    const user = userEvent.setup();
    render(<VignettePlayer beats={MOCK_LESSON.vignette} revealed={1} vocab={MOCK_LESSON.target_vocab} />);
    // "bisita" is in target_vocab; "Marami" is not.
    expect(screen.queryByRole("button", { name: /^Marami/ })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /bisita/ }));
    const sheet = await screen.findByRole("dialog");
    expect(sheet).toHaveTextContent("bisita");
    expect(sheet).toHaveTextContent("guest");
    expect(sheet).toHaveTextContent("noun");
  });

  it("matches vocabulary regardless of case and trailing punctuation", async () => {
    const user = userEvent.setup();
    render(<VignettePlayer beats={MOCK_LESSON.vignette} revealed={3} vocab={MOCK_LESSON.target_vocab} />);
    // "hapunan" appears in line 1; "Dumating" (capitalized) in line 3 matches "dumating".
    await user.click(screen.getByRole("button", { name: /^Dumating/ }));
    expect(await screen.findByRole("dialog")).toHaveTextContent("arrived");
  });
});
