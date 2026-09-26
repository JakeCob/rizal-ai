/**
 * Behaviors (plan 012, D39): the flag's eight-ray sun as an inline SVG.
 * - decorative: aria-hidden, and data-motif so the layout gate skips it
 * - one disc and eight ray paths, filled with currentColor so a text-*
 *   class colors it; the disc (radius 5.75) and the rays (a 4-unit base)
 *   fill the 24px box like a lucide icon does
 * - it reads as the flag's sun, a disc with separate rays: every ray starts
 *   clear of the disc, leaving a ring of background between them
 * - 24x24 by default like a lucide icon, so it swaps in without moving
 *   anything; className passes through
 */
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Sun } from "./Sun";

describe("Sun", () => {
  it("is a decorative 24px svg with a disc and eight rays in currentColor", () => {
    const { container } = render(<Sun />);
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
    expect(svg).toHaveAttribute("aria-hidden", "true");
    expect(svg).toHaveAttribute("data-motif");
    expect(svg).toHaveAttribute("width", "24");
    expect(svg).toHaveAttribute("height", "24");
    expect(svg).toHaveAttribute("viewBox", "0 0 24 24");
    expect(svg).toHaveAttribute("fill", "currentColor");
    expect(svg?.querySelectorAll("circle")).toHaveLength(1);
    expect(svg?.querySelector("circle")).toHaveAttribute("r", "5.75");
    const rays = svg?.querySelectorAll("path") ?? [];
    expect(rays).toHaveLength(8);
    const angles = [...rays].map((r) => r.getAttribute("transform"));
    expect(new Set(angles).size).toBe(8);
    // The ray: a triangle from the top of the box (y 0.75) down to a 4-unit
    // base that stops short of the disc (radius 5.75) by more than half a unit.
    const [tip, right, left] = (rays[0].getAttribute("d") ?? "").match(/-?[\d.]+\s+-?[\d.]+/g)?.map((p) => p.split(/\s+/).map(Number)) ?? [];
    expect(tip).toEqual([12, 0.75]);
    expect(right[0] - left[0]).toBeCloseTo(4, 5);
    expect(right[1]).toBe(left[1]);
    expect(12 - right[1]).toBeGreaterThan(5.75 + 0.5);
    expect(svg?.querySelector("[id]")).toBeNull();
  });

  it("passes className and other svg props through", () => {
    const { container } = render(<Sun className="text-accent size-40" data-testid="s" />);
    const svg = container.querySelector("svg");
    expect(svg).toHaveClass("text-accent", "size-40");
    expect(svg).toHaveAttribute("data-testid", "s");
  });
});
