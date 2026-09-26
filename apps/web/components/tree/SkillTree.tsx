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
    <div className="flex flex-col gap-8 pb-24 md:gap-12 xl:mx-auto xl:w-full xl:max-w-2xl">
      {tree.units.map((unit) => (
        <section key={unit.id} aria-labelledby={`unit-${unit.id}`}>
          <header className="sticky top-0 z-10 -mx-4 bg-primary px-5 py-3 text-primary-foreground shadow-sm md:mx-0 md:rounded-2xl">
            <p className="text-xs font-bold uppercase tracking-wider opacity-90">Unit {unit.order_index}</p>
            <h2 id={`unit-${unit.id}`} className="text-lg font-extrabold leading-tight md:scroll-mt-20">
              {unit.title}
            </h2>
          </header>
          <ol className="mt-6 flex flex-col items-center gap-6 md:gap-8">
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
  // Full class strings so Tailwind sees them. The phone swing is the original
  // eight-step pattern; from md the path column is wider and a four-step
  // pattern (center, right, center, left) swings both ways around the
  // center, so a short unit does not drift to one side.
  const phone = ["translate-x-0", "translate-x-10", "translate-x-14", "translate-x-10", "translate-x-0", "-translate-x-10", "-translate-x-14", "-translate-x-10"];
  const wide = ["md:translate-x-0", "md:translate-x-20", "md:translate-x-0", "md:-translate-x-20"];
  return `${phone[i % phone.length]} ${wide[i % wide.length]}`;
}
