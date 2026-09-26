import { Progress } from "@/components/ui/progress";
import { currentUnitId, unitProgress } from "@/lib/tree/summary";
import { cn } from "@/lib/utils";
import type { TreeUnit } from "@/lib/types.generated";

/**
 * The units list beside the path from 768px up (plan 010). Each link points
 * at the unit's heading; a click scrolls the unit's section to the top
 * instead, because the heading is sticky and can sit at the bottom of an
 * earlier section. Smooth only when the user has not asked for less motion.
 * The unit holding the active lesson (else the first) carries
 * aria-current="true" and a tinted state. The list's negative margin cancels
 * the links' padding, so the text lines up with the wordmark above.
 */
export function UnitNav({ units }: { units: TreeUnit[] }) {
  const current = currentUnitId(units);
  return (
    <nav aria-label="Units" className="flex flex-col gap-2">
      <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Units</p>
      <ul className="-mx-2 flex flex-col gap-1">
        {units.map((unit) => {
          const { done, total, fraction } = unitProgress(unit);
          const isCurrent = unit.id === current;
          return (
            <li key={unit.id}>
              <a
                href={`#unit-${unit.id}`}
                aria-current={isCurrent ? "true" : undefined}
                onClick={(event) => {
                  const section = document.getElementById(`unit-${unit.id}`)?.closest("section");
                  if (!section) return;
                  event.preventDefault();
                  section.scrollIntoView({ behavior: prefersReducedMotion() ? "auto" : "smooth", block: "start" });
                }}
                className={cn(
                  "flex flex-col gap-1.5 rounded-xl px-2 py-2 hover:bg-muted focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring/50",
                  isCurrent && "bg-primary-tint hover:bg-primary-tint",
                )}
              >
                <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Unit {unit.order_index}</span>
                <span className={cn("text-sm font-extrabold leading-snug", isCurrent && "text-primary-text")}>{unit.title}</span>
                <Progress
                  value={fraction * 100}
                  aria-label={`${unit.title} progress`}
                  className="[&_[data-slot=progress-track]]:h-1.5 [&_[data-slot=progress-track]]:bg-border"
                />
                <span className="text-xs text-muted-foreground">
                  {done} of {total} done
                </span>
              </a>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

function prefersReducedMotion(): boolean {
  return typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}
