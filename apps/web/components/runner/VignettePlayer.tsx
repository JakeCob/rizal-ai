"use client";

import { Volume2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Beat } from "@/lib/types.generated";

/**
 * Line-by-line reveal. Revealed lines stay on screen; earlier ones dim and
 * the current one is bright (docs/ui-references.md section 4).
 */
export function VignettePlayer({ beats, revealed }: { beats: readonly Beat[]; revealed: number }) {
  return (
    <ol className="flex flex-col gap-5" aria-label="Story">
      {beats.slice(0, revealed + 1).map((beat, i) => {
        const dimmed = i < revealed;
        return (
          <li
            key={beat.line_id}
            data-dimmed={dimmed ? "true" : "false"}
            aria-current={dimmed ? undefined : "step"}
            className={cn("flex flex-col gap-1 transition-opacity duration-200", dimmed ? "opacity-45" : "opacity-100")}
          >
            {beat.speaker && (
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">{beat.speaker}</p>
            )}
            <div className="flex items-start gap-3">
              <button
                type="button"
                aria-label={`Play line ${i + 1}`}
                disabled={!beat.audio_url}
                onClick={() => beat.audio_url && new Audio(beat.audio_url).play()}
                className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary disabled:opacity-30"
              >
                <Volume2 aria-hidden className="h-5 w-5" />
              </button>
              <div>
                <p lang="tl" className="text-lg font-bold leading-snug">
                  {beat.tl}
                </p>
                <p lang="en" className="text-sm text-muted-foreground">
                  {beat.en}
                </p>
              </div>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
