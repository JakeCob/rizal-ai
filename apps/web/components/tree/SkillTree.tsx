"use client";

import type { Tree } from "@/lib/types.generated";
import { PathNode } from "./PathNode";

/**
 * Vertical path of units and lessons. One header band per unit, nodes in a
 * gentle zigzag, three states: locked, active, done (docs/ui-references.md
 * section 2).
 */
export function SkillTree({ tree }: { tree: Tree }) {
  return (
    <div className="flex flex-col gap-8 pb-24">
      {tree.units.map((unit) => (
        <section key={unit.id} aria-labelledby={`unit-${unit.id}`}>
          <header className="sticky top-0 z-10 -mx-4 bg-primary px-5 py-3 text-primary-foreground shadow-sm">
            <p className="text-xs font-bold uppercase tracking-wider opacity-80">Unit {unit.order_index}</p>
            <h2 id={`unit-${unit.id}`} className="text-lg font-extrabold leading-tight">
              {unit.title}
            </h2>
          </header>
          <ol className="mt-6 flex flex-col items-center gap-6">
            {unit.lessons.map((lesson, i) => (
              <li key={lesson.id} className={zigzag(i)}>
                <PathNode lesson={lesson} />
              </li>
            ))}
          </ol>
        </section>
      ))}
    </div>
  );
}

function zigzag(i: number): string {
  const pattern = ["translate-x-0", "translate-x-10", "translate-x-14", "translate-x-10", "translate-x-0", "-translate-x-10", "-translate-x-14", "-translate-x-10"];
  return pattern[i % pattern.length];
}
