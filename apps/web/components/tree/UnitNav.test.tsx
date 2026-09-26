/**
 * Behaviors:
 * - a nav landmark named Units with one link per unit, href #unit-{id}
 * - each link shows the unit's done over total and a progress bar
 * - the current unit (the one holding the active lesson, else the first) is
 *   marked with aria-current="true"; the others carry no aria-current
 * - clicking a link scrolls the unit's section into view (smooth unless the
 *   user asks for reduced motion) instead of jumping to the sticky heading
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { TreeLesson, TreeUnit } from "@/lib/types.generated";
import { UnitNav } from "./UnitNav";

function lesson(id: string, status: TreeLesson["status"]): TreeLesson {
  return { id, slug: id, title: id, order_index: 0, status, xp_reward: 10, estimated_minutes: 3 };
}

const UNITS: TreeUnit[] = [
  { id: "u1", slug: "u1", title: "Ibarra's return", order_index: 1, lessons: [lesson("a", "done"), lesson("b", "active")] },
  { id: "u2", slug: "u2", title: "The sermon", order_index: 2, lessons: [lesson("c", "locked")] },
];

afterEach(() => {
  vi.unstubAllGlobals();
  document.body.innerHTML = "";
});

describe("UnitNav", () => {
  it("renders one link per unit pointing at its heading", () => {
    render(<UnitNav units={UNITS} />);
    const nav = screen.getByRole("navigation", { name: "Units" });
    const links = screen.getAllByRole("link");
    expect(nav).toContainElement(links[0]);
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute("href", "#unit-u1");
    expect(links[1]).toHaveAttribute("href", "#unit-u2");
    expect(links[0]).toHaveTextContent("Ibarra's return");
  });

  it("shows done over total and a progress bar per unit", () => {
    render(<UnitNav units={UNITS} />);
    const links = screen.getAllByRole("link");
    expect(links[0]).toHaveTextContent("1 of 2 done");
    expect(links[1]).toHaveTextContent("0 of 1 done");
    const bars = screen.getAllByRole("progressbar");
    expect(bars).toHaveLength(2);
    expect(bars[0]).toHaveAttribute("aria-valuenow", "50");
  });

  it("scrolls the unit's section into view on click", async () => {
    const user = userEvent.setup();
    const section = document.createElement("section");
    const heading = document.createElement("h2");
    heading.id = "unit-u2";
    section.appendChild(heading);
    document.body.appendChild(section);
    const spy = vi.fn();
    section.scrollIntoView = spy;
    render(<UnitNav units={UNITS} />);
    await user.click(screen.getByRole("link", { name: /The sermon/ }));
    expect(spy).toHaveBeenCalledWith({ behavior: "smooth", block: "start" });
  });

  it("jumps without animation under reduced motion", async () => {
    vi.stubGlobal("matchMedia", (q: string) => ({ matches: q.includes("reduce"), media: q }));
    const user = userEvent.setup();
    const section = document.createElement("section");
    const heading = document.createElement("h2");
    heading.id = "unit-u1";
    section.appendChild(heading);
    document.body.appendChild(section);
    const spy = vi.fn();
    section.scrollIntoView = spy;
    render(<UnitNav units={UNITS} />);
    await user.click(screen.getByRole("link", { name: /Ibarra's return/ }));
    expect(spy).toHaveBeenCalledWith({ behavior: "auto", block: "start" });
  });

  it("marks the unit with the active lesson as current", () => {
    render(<UnitNav units={UNITS} />);
    const links = screen.getAllByRole("link");
    expect(links[0]).toHaveAttribute("aria-current", "true");
    expect(links[1]).not.toHaveAttribute("aria-current");
  });

  it("marks the first unit as current when no lesson is active", () => {
    const done: TreeUnit[] = [
      { ...UNITS[0], lessons: [lesson("a", "done")] },
      { ...UNITS[1], lessons: [lesson("c", "locked")] },
    ];
    render(<UnitNav units={done} />);
    const links = screen.getAllByRole("link");
    expect(links[0]).toHaveAttribute("aria-current", "true");
    expect(links[1]).not.toHaveAttribute("aria-current");
  });
});
