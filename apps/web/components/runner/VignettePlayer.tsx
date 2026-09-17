"use client";

import { useMemo, useState } from "react";
import { Volume2 } from "lucide-react";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import type { Beat, VocabItem } from "@/lib/types.generated";

/**
 * Line-by-line reveal. Revealed lines stay on screen; earlier ones dim and
 * the current one is bright (docs/ui-references.md section 4). Tagalog
 * words that are in the lesson's target vocabulary are tappable and open a
 * gloss sheet; the gloss comes from the lesson, never from the network.
 */
export function VignettePlayer({
  beats,
  revealed,
  vocab = [],
}: {
  beats: readonly Beat[];
  revealed: number;
  vocab?: readonly VocabItem[];
}) {
  const [selected, setSelected] = useState<VocabItem | null>(null);
  const glossary = useMemo(() => new Map(vocab.map((v) => [normalize(v.tl), v])), [vocab]);

  return (
    <>
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
                    <Words text={beat.tl} glossary={glossary} onPick={setSelected} />
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

      <Sheet open={selected !== null} onOpenChange={(open) => !open && setSelected(null)}>
        <SheetContent side="bottom" className="rounded-t-3xl px-5 pb-8 pt-5" aria-label="Word gloss">
          {selected && (
            <div className="flex flex-col gap-1">
              <p lang="tl" className="text-2xl font-extrabold">
                {selected.tl}
              </p>
              <p className="text-lg">{selected.en}</p>
              {selected.pos && <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">{selected.pos}</p>}
              {selected.note && <p className="text-sm text-muted-foreground">{selected.note}</p>}
            </div>
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}

function normalize(word: string): string {
  return word.toLowerCase().replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, "");
}

function Words({
  text,
  glossary,
  onPick,
}: {
  text: string;
  glossary: Map<string, VocabItem>;
  onPick: (item: VocabItem) => void;
}) {
  const parts = text.split(/(\s+)/);
  return (
    <>
      {parts.map((part, i) => {
        if (/^\s+$/.test(part) || part === "") return part;
        const item = glossary.get(normalize(part));
        if (!item) return <span key={i}>{part}</span>;
        return (
          <button
            key={i}
            type="button"
            onClick={() => onPick(item)}
            className="rounded-md underline decoration-primary/50 decoration-2 underline-offset-4 hover:bg-primary/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {part}
          </button>
        );
      })}
    </>
  );
}
