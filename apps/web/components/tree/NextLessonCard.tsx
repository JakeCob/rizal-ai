import Link from "next/link";
import { cn } from "@/lib/utils";
import type { NextLesson } from "@/lib/tree/summary";

/**
 * The next lesson in the desktop progress column (plan 010). The link is
 * named "Go to lesson" so the phone popover keeps the only "Start" link.
 */
export function NextLessonCard({ next }: { next: NextLesson | null }) {
  if (!next) {
    return (
      <section className="rounded-2xl border-2 border-border bg-card p-4">
        <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Up next</h2>
        <p className="mt-2 text-base font-extrabold">All caught up</p>
        <p className="mt-1 text-sm text-muted-foreground">No lesson is waiting. New lessons open here as the path grows.</p>
      </section>
    );
  }
  const { unit, lesson } = next;
  return (
    <section className="rounded-2xl border-2 border-primary/30 bg-primary/5 p-4">
      <h2 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Up next</h2>
      <p className="mt-2 text-xs font-bold text-muted-foreground">{unit.title}</p>
      <p className="mt-1 text-base font-extrabold leading-snug">{lesson.title}</p>
      <p className="mt-1 text-sm text-muted-foreground">
        {lesson.estimated_minutes} min · {lesson.xp_reward} XP
      </p>
      <Link
        href={`/lesson/${lesson.id}`}
        className={cn(
          "mt-4 flex h-12 w-full items-center justify-center rounded-xl bg-primary text-sm font-extrabold uppercase tracking-wide text-primary-foreground",
          "shadow-[0_4px_0_0_var(--primary-lip)] active:translate-y-1 active:shadow-none",
          "focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring/50",
        )}
      >
        Go to lesson
      </Link>
    </section>
  );
}
