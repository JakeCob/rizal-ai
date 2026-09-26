/**
 * Behaviors:
 * - nextLesson returns the single active lesson in path order, with its unit,
 *   or null when no lesson is active (every lesson done, or none unlocked)
 * - unitProgress counts done lessons over all lessons, locked placeholders
 *   included, and reports an empty unit as 0 of 0
 * - currentUnitId is the unit holding the active lesson, else the first
 *   unit, else null for an empty tree
 */
import { describe, expect, it } from "vitest";
import { MOCK_TREE } from "@/lib/api/fixtures";
import type { Tree, TreeLesson, TreeUnit } from "@/lib/types.generated";
import { currentUnitId, nextLesson, unitProgress } from "./summary";

function lesson(id: string, status: TreeLesson["status"]): TreeLesson {
  return { id, slug: id, title: `Lesson ${id}`, order_index: 0, status, xp_reward: 10, estimated_minutes: 3 };
}

function unit(id: string, lessons: TreeLesson[]): TreeUnit {
  return { id, slug: id, title: `Unit ${id}`, order_index: 1, lessons };
}

describe("nextLesson", () => {
  it("returns the active lesson and its unit", () => {
    const next = nextLesson(MOCK_TREE);
    expect(next?.lesson.title).toBe("Placeholder: the dinner at Capitan Tiago's");
    expect(next?.unit.id).toBe(MOCK_TREE.units[0].id);
  });

  it("finds the active lesson in a later unit", () => {
    const tree: Tree = {
      units: [unit("u1", [lesson("a", "done"), lesson("b", "done")]), unit("u2", [lesson("c", "active"), lesson("d", "locked")])],
    };
    expect(nextLesson(tree)?.lesson.id).toBe("c");
    expect(nextLesson(tree)?.unit.id).toBe("u2");
  });

  it("returns null when every lesson is done", () => {
    const tree: Tree = { units: [unit("u1", [lesson("a", "done"), lesson("b", "done")])] };
    expect(nextLesson(tree)).toBeNull();
  });

  it("returns null for an empty tree", () => {
    expect(nextLesson({ units: [] })).toBeNull();
  });
});

describe("unitProgress", () => {
  it("counts done over total, locked placeholders included", () => {
    const u = unit("u1", [lesson("a", "done"), lesson("b", "active"), lesson("c", "locked"), lesson("d", "locked")]);
    expect(unitProgress(u)).toEqual({ done: 1, total: 4, fraction: 0.25 });
  });

  it("reports an empty unit as 0 of 0 without dividing by zero", () => {
    expect(unitProgress(unit("u1", []))).toEqual({ done: 0, total: 0, fraction: 0 });
  });
});

describe("currentUnitId", () => {
  it("is the unit holding the active lesson", () => {
    const units = [unit("u1", [lesson("a", "done")]), unit("u2", [lesson("b", "active")])];
    expect(currentUnitId(units)).toBe("u2");
  });

  it("falls back to the first unit when no lesson is active", () => {
    const units = [unit("u1", [lesson("a", "done")]), unit("u2", [lesson("b", "locked")])];
    expect(currentUnitId(units)).toBe("u1");
  });

  it("is null for no units", () => {
    expect(currentUnitId([])).toBeNull();
  });
});
