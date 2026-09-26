"use client";

import Link from "next/link";
import { Check, Lock, Star } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import type { TreeLesson } from "@/lib/types.generated";

const STATUS_LABEL: Record<TreeLesson["status"], string> = {
  locked: "locked",
  active: "active",
  done: "done",
};

export function PathNode({ lesson }: { lesson: TreeLesson }) {
  const locked = lesson.status === "locked";
  const label = `${lesson.title}, ${STATUS_LABEL[lesson.status]}`;

  const button = (
    <button
      type="button"
      disabled={locked}
      aria-label={label}
      data-status={lesson.status}
      className={cn(
        "relative flex h-[72px] w-[72px] items-center justify-center rounded-3xl text-2xl transition-transform md:h-24 md:w-24 md:text-3xl",
        "shadow-[0_5px_0_0_var(--lip)] active:translate-y-[5px] active:shadow-none",
        "focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring/50",
        lesson.status === "active" && "bg-primary text-primary-foreground [--lip:var(--primary-lip)]",
        lesson.status === "done" && "bg-accent text-accent-foreground [--lip:var(--accent-lip)]",
        locked && "cursor-not-allowed bg-muted text-muted-foreground [--lip:var(--muted-lip)]",
      )}
    >
      {lesson.status === "done" ? <Check aria-hidden /> : locked ? <Lock aria-hidden /> : <Star aria-hidden />}
      {lesson.status === "active" && (
        <span aria-hidden className="absolute -inset-2 -z-10 rounded-[2rem] border-4 border-primary/25 md:-inset-3" />
      )}
    </button>
  );

  if (locked) return button;

  return (
    <Popover>
      <PopoverTrigger render={button} />
      <PopoverContent align="center" sideOffset={12} className="w-64 rounded-2xl p-4">
        <p className="text-base font-extrabold leading-snug">{lesson.title}</p>
        <p className="mt-1 text-sm text-muted-foreground">
          {lesson.estimated_minutes} min · {lesson.xp_reward} XP
        </p>
        <Link
          href={`/lesson/${lesson.id}`}
          className={cn(
            "mt-4 flex h-12 w-full items-center justify-center rounded-xl bg-primary text-sm font-extrabold uppercase tracking-wide text-primary-foreground",
            "shadow-[0_4px_0_0_var(--primary-lip)] active:translate-y-1 active:shadow-none",
          )}
        >
          {lesson.status === "done" ? "Review" : "Start"}
        </Link>
      </PopoverContent>
    </Popover>
  );
}
