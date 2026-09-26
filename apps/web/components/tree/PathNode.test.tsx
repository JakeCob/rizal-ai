/**
 * Behaviors (plan 012): the active node shows the eight-ray sun in accent
 * gold instead of the lucide star; done and locked nodes keep their check
 * and lock.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { TreeLesson } from "@/lib/types.generated";
import { PathNode } from "./PathNode";

function lesson(status: TreeLesson["status"]): TreeLesson {
  return { id: `l-${status}`, slug: status, title: `Lesson ${status}`, order_index: 0, status, xp_reward: 10, estimated_minutes: 3 };
}

describe("PathNode icons", () => {
  it("draws the sun in accent gold on the active node, not the star", () => {
    render(<PathNode lesson={lesson("active")} />);
    const node = screen.getByRole("button", { name: /Lesson active/ });
    const sun = node.querySelector("svg[data-motif]");
    expect(sun).not.toBeNull();
    expect(sun).toHaveClass("text-accent");
    expect(node.querySelector("svg.lucide-star")).toBeNull();
  });

  it("keeps the check on done and the lock on locked nodes, with no sun", () => {
    const { container } = render(
      <>
        <PathNode lesson={lesson("done")} />
        <PathNode lesson={lesson("locked")} />
      </>,
    );
    expect(container.querySelector("svg.lucide-check")).not.toBeNull();
    expect(container.querySelector("svg.lucide-lock")).not.toBeNull();
    expect(container.querySelector("svg[data-motif]")).toBeNull();
  });
});

describe("PathNode halo", () => {
  it("rings the active node in primary in light and in accent gold in dark (3:1 on the navy page)", () => {
    render(<PathNode lesson={lesson("active")} />);
    const ring = screen.getByRole("button", { name: /Lesson active/ }).querySelector("span[aria-hidden]");
    expect(ring).toHaveClass("border-primary/25", "dark:border-accent/60");
  });
});
