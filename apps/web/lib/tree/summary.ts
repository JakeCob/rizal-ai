import type { Tree, TreeLesson, TreeUnit } from "@/lib/types.generated";

/**
 * Pure summaries of the tree for the desktop columns (plan 010). They read
 * the tree the page already has, so the columns cost no request (D14).
 */

export type NextLesson = { unit: TreeUnit; lesson: TreeLesson };

/** The API marks at most one lesson active, in path order; that is the next one. */
export function nextLesson(tree: Tree): NextLesson | null {
  for (const unit of tree.units) {
    const lesson = unit.lessons.find((l) => l.status === "active");
    if (lesson) return { unit, lesson };
  }
  return null;
}

/** Done lessons over all lessons in the unit, locked placeholders included. */
export function unitProgress(unit: TreeUnit): { done: number; total: number; fraction: number } {
  const total = unit.lessons.length;
  const done = unit.lessons.filter((l) => l.status === "done").length;
  return { done, total, fraction: total === 0 ? 0 : done / total };
}

/** The unit to mark as current in the nav: the one holding the active lesson, else the first. */
export function currentUnitId(units: TreeUnit[]): string | null {
  const withActive = units.find((u) => u.lessons.some((l) => l.status === "active"));
  return (withActive ?? units[0])?.id ?? null;
}
